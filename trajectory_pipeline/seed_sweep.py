"""Cold date/KLO survey followed only by independently verified IRT.

The initial KLO duration is an explicit screening estimate, not proof that
other numerical roots or physical trajectories outside the catalogue do not exist.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace
from datetime import datetime,timedelta
from pathlib import Path
import json,subprocess,sys,time
from threading import Lock
import numpy as np
from .data import DAY_S,Scales,Trajectory,write_json,sha256
from .problem import Mission
from .iltt_entry import angular_branches,date_entry
from .ephemerides import Ephemerides
from .runtime import runtime_environment
from .verification import verify_irt

_VERIFY_LOCK=Lock()  # SciPy LSODA replay is not reentrant within one process.


def catalogue(mission,design):
    required={'start_tdb','stop_tdb','step_days','max_duration_days','max_abs_k','workers','worker_timeout_s','iltt_budget_s','irt_budget_s'}
    if set(design)!=required:raise ValueError('Seed sweep design keys differ: '+str(set(design)^required))
    if not date_entry(mission) or mission.mode!='rendezvous' or mission.time_policy is not None:
        raise ValueError('Early sweep requires date-first central rendezvous without a time policy')
    for key in required-{'start_tdb','stop_tdb'}:
        if type(design[key]) not in (int,float) or not np.isfinite(design[key]) or design[key]<=0:raise ValueError('Invalid '+key)
    for key in ('max_abs_k','workers'):
        if type(design[key]) is not int:raise ValueError(key+' must be an integer')
    first=datetime.fromisoformat(design['start_tdb']);last=datetime.fromisoformat(design['stop_tdb'])
    if first.tzinfo or last.tzinfo or last<first:raise ValueError('Invalid TDB date range')
    eph=mission.ephemerides();rows=[];requests=[];i=0
    while first+timedelta(days=i*design['step_days'])<=last:
        date=(first+timedelta(days=i*design['step_days'])).isoformat();i+=1
        settings={k:v for k,v in mission.solver.items() if k not in ('iltt_resolved','iltt_branch','iltt_duration_bounds_days')}
        settings.update(irt_entry='date',iltt_max_abs_k=design['max_abs_k'],iltt_budget_s=design['iltt_budget_s'],
                        budget_s=design['irt_budget_s'],attempt_budget_s=design['irt_budget_s'],compare_seeds=False)
        current=replace(mission,launch_tdb=date,tof_days=None,solver=settings)
        row=dict(launch_tdb=date,candidates=[])
        try:
            tb,_,scale,initial,el,phase,branches=angular_branches(current,eph)
            row.update(phase_rad=phase,kappa=float(el[0]))
            for rank,b in enumerate(branches):
                candidate=dict(branch_rank=rank,**b)
                try:
                    duration=float(2*np.pi*tb.T_a(b['lambda_initial'],float(el[0]))*scale.time_s/DAY_S)
                    candidate['estimated_duration_days']=duration if np.isfinite(duration) else None
                    if not np.isfinite(duration) or duration<=0:candidate.update(status='screened',reason='invalid_KLO_duration')
                    elif duration>design['max_duration_days']:candidate.update(status='screened',reason='KLO_duration_above_horizon')
                    else:
                        # Filter the derived KLO candidate, never fit lambda to a requested time.
                        candidate['ephemeris_evaluation']={body:eph.evaluation_record(body,[current.launch_jd,current.launch_jd+duration]) for body in (current.departure,current.target)}
                        identity=f'date_{i-1:04d}_branch_{rank:02d}'
                        resolved=replace(current,case_id=identity,solver=dict(settings,iltt_branch=rank,
                            iltt_duration_bounds_days=[1e-8,design['max_duration_days']]))
                        candidate.update(status='pending',case_id=identity)
                        requests.append(resolved.to_dict())
                except Exception as exc:candidate.update(status='screened',reason=type(exc).__name__+': '+str(exc))
                row['candidates'].append(candidate)
        except Exception as exc:row.update(error=type(exc).__name__+': '+str(exc))
        rows.append(row)
    return rows,requests


def collect_case(folder,mission,process_error=None):
    row=dict(case_id=mission.case_id,launch_tdb=mission.launch_tdb,branch_rank=mission.solver['iltt_branch'],
             status='failed',phase='iltt_entry')
    summary_path=folder/'summary.json'
    summary=json.loads(summary_path.read_text()) if summary_path.exists() else {}
    if (folder/'mission.json').exists():row['phase']='irt'
    row['error']=process_error or summary.get('error')
    if summary.get('status')=='completed_stage' and not process_error:
        artifact=folder/summary['last_result'];result=Trajectory.load(artifact)
        with _VERIFY_LOCK:check=verify_irt(result)
        if not check['passed']:raise ValueError('Independent IRT replay changed')
        model=result.metadata['mission']
        for key in ('launch_tdb','departure','target','mass_kg','spacecraft'):
            if model[key]!=mission.to_dict()[key]:raise ValueError('Changed sweep input '+key)
        if result.metadata['chosen_seed']['source'] not in ('ILTT date/phase','ILTT date/phase approximation'):raise ValueError('Non-KLO seed')
        from .contract import audit_configuration,make_request
        audit_configuration(result,replace(mission,tof_days=model['tof_days']),make_request(replace(mission,tof_days=model['tof_days'])))
        if not 0<model['tof_days']<=mission.solver['iltt_duration_bounds_days'][1]:raise ValueError('IRT outside horizon')
        entry=model['solver'].get('iltt_resolved',{})
        fallback=model['solver'].get('irt_date_fallback',{})
        scales=Scales(**result.metadata['scales']);J=float(result.metadata['functional_dimensionless'])
        row.update(status='accepted',phase='irt',error=None,artifact=str(artifact),duration_days=model['tof_days'],
                   lambda_corrected=entry.get('lambda_corrected'),
                   k=entry.get('k',fallback.get('branch',{}).get('k')),entry_route=result.metadata.get('entry_route'),functional_dimensionless=J,
                   functional_si_m2_s3=J*scales.acceleration_m_s2**2*scales.time_s,
                   verification=check,arrays_sha256=sha256(artifact/'trajectory.npz'),metadata_sha256=sha256(artifact/'trajectory.json'))
    if summary.get('elapsed_s') is not None:row['solver_elapsed_s']=summary['elapsed_s']
    return row


def summarize(catalog,results):
    table={r['case_id']:r for r in results};dates=[]
    for entry in catalog:
        attempted=[table[c['case_id']] for c in entry['candidates'] if c.get('case_id') in table]
        accepted=[x for x in attempted if x['status']=='accepted']
        pending=sum(c.get('case_id') not in table for c in entry['candidates'] if c.get('case_id'))
        best=min(accepted,key=lambda x:x['functional_si_m2_s3']) if accepted else None
        dates.append(dict(launch_tdb=entry['launch_tdb'],status='accepted' if best else 'pending' if pending else 'no_verified_IRT' if attempted else 'no_KLO_candidate_in_horizon',
                          accepted=len(accepted),attempted=len(attempted),pending=pending,selected=best))
    return dict(dates=dates,totals=dict(dates=len(dates),accepted_dates=sum(r['selected'] is not None for r in dates),
            candidate_runs=len(table),accepted_branches=sum(r['status']=='accepted' for r in results),
            screened_candidates=sum(c['status']=='screened' for r in catalog for c in r['candidates'])),
            selection='Minimum dimensional integral |acceleration|^2/2 dt among independently accepted IRT candidates per date',
            scope='KLO initial-duration screen and IRT at derived fixed duration only; no impulse, Pazov, PSI or fuel claim',
            completeness='Finite k catalogue; failures and initial-duration screening exclude a claim of a global minimum')


def run_seed_sweep(mission,design,output,resume=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=resume)
    root=Path(__file__).resolve().parents[1]
    provenance=dict(mission=mission.to_dict(),design=design,runtime=runtime_environment(),
        source_sha256={str(p.relative_to(root)):sha256(p) for p in sorted((root/'trajectory_pipeline').glob('*.py'))},
        toolbox_sha256=sha256(root/'ILTT/ILTTToolbox.py'),
        ephemerides_sha256={str(p.relative_to(root)):sha256(p) for p in sorted((root/'data/ephemerides').rglob('*')) if p.is_file() and p.suffix in ('.npz','.json')})
    manifest=output/'request.json'
    if manifest.exists():
        old=json.loads(manifest.read_text())
        if old!=provenance:raise ValueError('Resume changed inputs, code, data or runtime')
    else:write_json(manifest,provenance)
    if (output/'catalogue.json').exists():
        catalog=json.loads((output/'catalogue.json').read_text());requests=json.loads((output/'missions.json').read_text())
    else:
        catalog,requests=catalogue(mission,design);write_json(output/'catalogue.json',catalog);write_json(output/'missions.json',requests)
    inputs=output/'inputs';inputs.mkdir(exist_ok=True);(output/'cases').mkdir(exist_ok=True)
    def work(raw):
        m=Mission(**raw);folder=output/'cases'/m.case_id;cached=folder/'sweep_result.json'
        if cached.exists():
            saved=json.loads(cached.read_text())
            if saved['status']=='accepted':
                if sha256(Path(saved['artifact'])/'trajectory.npz')!=saved['arrays_sha256'] or sha256(Path(saved['artifact'])/'trajectory.json')!=saved['metadata_sha256']:
                    raise ValueError('Cached IRT changed')
            return saved
        request=inputs/(m.case_id+'.json');write_json(request,m.to_dict());start=time.perf_counter();error=None
        if folder.exists():
            row=collect_case(folder,m,'Interrupted prior attempt; preserved without automatic rerun')
        else:
            log=output/(m.case_id+'.log')
            with log.open('w') as stream:
                try:
                    done=subprocess.run([sys.executable,'-m','trajectory_pipeline','solve-irt',str(request),'--output',str(folder)],
                                        stdout=stream,stderr=subprocess.STDOUT,timeout=max(design['worker_timeout_s'],design['iltt_budget_s']+3*design['irt_budget_s']+30))
                    if done.returncode and not (folder/'summary.json').exists():error='Worker exit '+str(done.returncode)
                except subprocess.TimeoutExpired:error='Hard worker time limit'
            row=collect_case(folder,m,error)
        row['wall_s']=time.perf_counter()-start;folder.mkdir(exist_ok=True);write_json(cached,row);return row
    results=[]
    print(f"{len(catalog)} dates; {len(requests)} KLO candidates inside the initial duration horizon",flush=True)
    with ThreadPoolExecutor(max_workers=design['workers']) as pool:
        futures=[pool.submit(work,raw) for raw in requests]
        for future in as_completed(futures):
            result=future.result();results.append(result);results.sort(key=lambda r:r['case_id'])
            write_json(output/'results.json',results);write_json(output/'summary.json',summarize(catalog,results))
            print(f"{len(results)}/{len(requests)} {result['launch_tdb']} rank={result['branch_rank']} {result['status']} {result['phase']}",flush=True)
    summary=summarize(catalog,results);summary['status']='finished';write_json(output/'summary.json',summary)
    print(summary['totals'],flush=True);return summary
