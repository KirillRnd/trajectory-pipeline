"""Continue accepted IRT artifacts without rebuilding or relabelling the seed."""
import argparse,json,traceback
from copy import deepcopy
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
from .data import Trajectory,write_json,sha256
from .problem import Mission
from .contract import audit_configuration,make_request
from .verification import verify_irt
from .bounded import verify_bounded
from .kiam_verification import verify_kiam_psi
from .departure import run_departure
from .pazov import run_pazov
from .psi import run_psi
from .intermediate_time import verify_intermediate,continue_physical_model,release_intermediate_duration
from .coordinate_matrix import timed_call

SETTINGS=dict(departure_budget_s=45,limit_budget_s=60,pazov_budget_s=60,psi_budget_s=90,
              bounded_attempt_s=15,exact_attempt_s=25,pipeline_pazov_alpha=.5,psi_mass_alpha=.5)


def physical(result, expected=None):
    m=Mission(**result.metadata['mission'])
    expected=m if expected is None else expected
    if result.metadata.get('stage')!='psi' or 'switch_times_s' not in result.metadata or 'initial_throttle' not in result.metadata:
        raise ValueError('Physical PSI requires exact active/passive arcs')
    audit=audit_configuration(result,expected,make_request(expected),require_final=True)
    check=verify_bounded(result);kiam=verify_kiam_psi(result)
    if not check['passed'] or not kiam['passed']:raise ValueError('Physical replay/KIAM check failed')
    return dict(verification=check,kiam_verification=kiam,parameter_audit=audit,
                tof_days=m.tof_days,fuel_kg=float(result.arrays['mass_kg'][0]-result.arrays['mass_kg'][-1]),
                final_mass_kg=float(result.arrays['mass_kg'][-1]),departure_m_s=result.metadata['departure']['norm_m_s'])


def checked_checkpoint(root,fallback):
    # Interrupted stages still keep each independently accepted continuation node.
    paths=sorted(Path(root).rglob('trajectory.json'),key=lambda p:p.stat().st_mtime,reverse=True)
    for p in paths:
        try:
            t=Trajectory.load(p.parent)
            if t.metadata.get('status')!='verified_extremal':continue
            if 'bounded_model' in t.metadata:
                if not verify_bounded(t)['passed']:continue
            elif not verify_irt(t)['passed']:continue
            audit_configuration(t,Mission(**t.metadata['mission']),make_request(Mission(**t.metadata['mission'])))
            return t
        except (ValueError,RuntimeError,KeyError):continue
    return fallback


def save_version(result,path):
    from .stage_journal import identity
    path=Path(path);candidate=path;index=1
    while candidate.exists():
        if (candidate/'trajectory.json').exists() and identity(Trajectory.load(candidate))==identity(result):return candidate
        index+=1;candidate=path.with_name(path.name+f'_{index:02d}')
    result.save(candidate);return candidate


def verify_stage(result):
    """Stage checkpoints may be either smooth intermediates or exact PSI."""
    if result.metadata.get('stage')=='psi':return physical(result)
    return verify_intermediate(result)


def run_case(request):
    case,rootstr,phase=request;root=Path(rootstr)/case['case_id'];root.mkdir(parents=True,exist_ok=True)
    path=root/(phase+'.json')
    if path.exists():
        cached=json.loads(path.read_text())
        if cached['status']=='completed':
            source=Trajectory.load(case['source'])
            final=Trajectory.load(cached['artifact'])
            physical(final,replace(Mission(**source.metadata['mission']),tof_days=final.metadata['mission']['tof_days']))
            return cached
    source=Trajectory.load(case['source']);original=Mission(**source.metadata['mission'])
    audit_configuration(source,original,make_request(original))
    if not verify_irt(source)['passed']:raise ValueError('Input IRT replay failed')
    settings=dict(SETTINGS,**case.get('settings',{}))
    phase_budget=4*settings['psi_budget_s']+60
    release_budget=float(settings.get('intermediate_release_budget_s',60))
    horizon=case.get('horizon_days',float('inf'))
    source.metadata['mission']['solver'].update(settings)
    current=source;history=[];result=dict(case_id=case['case_id'],phase=phase,status='partial',source=case['source'])
    began=perf_counter()
    def log(event):
        history.append(event);write_json(root/(phase+'_progress.json'),dict(events=history))
    def operation(name,fn,budget):
        nonlocal current
        from .stage_journal import stage
        def execute(seed,out):
            event=dict(operation=name,input_stage=seed.metadata.get('stage'),input_days=seed.metadata['mission']['tof_days'])
            try:
                # An interrupted non-IRT checkpoint resumes its remaining model
                # instead of resetting continuation parameters to zero.
                action=continue_physical_model if 'bounded_model' in seed.metadata else fn
                if seed.metadata.get('stage')=='psi':
                    physical(seed);return seed,dict(event,status='completed_stage')
                result,state=timed_call(budget,action,seed,out)
                event.update(status=state['status'],stopped_phase=state.get('phase'),details=state)
            except Exception as exc:
                event.update(status='exception',error=type(exc).__name__+': '+str(exc))
                result=checked_checkpoint(out,seed)
            return result,event
        current,event=stage(root,name,current,execute,verify_stage,recover=checked_checkpoint)
        event['checkpoint']=str(root/(name+'_checkpoint'));log(event)
        return event
    def accept(label):
        try:
            days=current.metadata['mission']['tof_days']
            if not 0<days<=horizon:raise ValueError('Duration exceeds requested horizon')
            check=physical(current,replace(original,tof_days=days))
        except (ValueError,RuntimeError,KeyError) as exc:
            log(dict(operation='physical_admission',status='failed',route=label,error=str(exc)))
            return False
        current.metadata.update(verification=check['verification'],kiam_verification=check['kiam_verification'])
        out=save_version(current,root/(phase+'_physical'));result.update(status='completed',artifact=str(out),route=label,**check)
        return True
    def release(name,seed,factor):
        nonlocal current
        from .stage_journal import stage
        t=original.tof_days;bounds=case.get('duration_bounds_days',[.5*t,min(factor*t,horizon)])
        def execute(initial,out):
            candidate=initial;event=dict(operation=name,bounds_days=bounds,input_days=initial.metadata['mission']['tof_days'])
            try:
                candidate=timed_call(release_budget+5,release_intermediate_duration,initial,bounds,perf_counter()+release_budget,out)
                event.update(status='completed_stage',output_days=candidate.metadata['mission']['tof_days'],details=candidate.metadata.get('intermediate_time'))
            except Exception as exc:event.update(status='failed',error=type(exc).__name__+': '+str(exc))
            return candidate,event
        current,event=stage(root,name,deepcopy(seed),execute,verify_intermediate,recover=checked_checkpoint)
        event['checkpoint']=str(root/(name+'_checkpoint'));log(event)
        return event['status']=='completed_stage'
    try:
        if phase=='primary':
            operation('departure',lambda s,o:run_departure(s,o),settings['departure_budget_s']+20)
            departure_ready=current.metadata.get('departure',{}).get('parameter',0)>=1-1e-10
            if departure_ready:
                operation('pazov',lambda s,o:run_pazov(s,o,target_alpha=settings['pipeline_pazov_alpha']),settings['limit_budget_s']+settings['pazov_budget_s']+25)
                if current.metadata.get('stage') in ('pazov','pazov_limit'):
                    operation('psi',lambda s,o:run_psi(s,o),phase_budget)
            accept(f"standard: departure -> Pazov({settings['pipeline_pazov_alpha']}) -> mass -> thrust -> fuel")
        elif phase=='recover':
            previous=json.loads((root/'primary.json').read_text())
            if previous['status']=='completed':return dict(case_id=case['case_id'],phase=phase,status='skipped_physical_parent')
            current=Trajectory.load(previous['last_checkpoint'])
            current.metadata['mission']['solver'].update(settings)
            try:verify_intermediate(current)
            except ValueError:
                # An exact but unaccepted endpoint must not erase the smooth parent.
                candidates=[root/'pazov_checkpoint',root/'departure_checkpoint']
                current=next((Trajectory.load(p) for p in candidates if (p/'trajectory.json').exists()),source)
            operation('coupled',continue_physical_model,phase_budget)
            if not accept('alternative: coupled mass/thrust'):
                if release('release_intermediate',current,1.5):
                    operation('after_release',continue_physical_model,phase_budget)
                    accept('intermediate duration -> coupled mass/thrust -> fuel')
            if result['status']!='completed':
                # A second path from an earlier model, not repetition at a stalled point.
                parent=Trajectory.load(root/'departure_checkpoint') if (root/'departure_checkpoint/trajectory.json').exists() else source
                parent.metadata['mission']['solver'].update(dict(settings,pipeline_pazov_alpha=.3,psi_mass_alpha=.3))
                release('release_early',parent,2.)
                operation('early_continue',continue_physical_model,phase_budget)
                accept('early duration -> Pazov(.3) -> coupled mass/thrust -> fuel')
        else:raise ValueError('Unknown phase')
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        (root/(phase+'_error.log')).write_text(traceback.format_exc())
    checkpoint=save_version(current,root/(phase+'_last'))
    result.update(events=history,last_checkpoint=str(checkpoint),last_stage=current.metadata.get('stage'),
                  last_model=current.metadata.get('bounded_model'),last_days=current.metadata['mission']['tof_days'],elapsed_s=perf_counter()-began)
    write_json(path,result);return result


def design(root,sources=None):
    archive=Path('data/benchmarks/coordinate_matrix_v1');rows=json.loads((archive/'final.json').read_text()) if sources is None else [];cases=[]
    for r in rows:
        if not r['accepted']:continue
        key=r['case_id']
        if r['target']=='Apophis':folder=archive/'apophis_full'/key/'irt'
        else:
            folder=archive/('next_branch' if r['branch']==1 else 'primary')/(key+('_branch1' if r['branch']==1 else ''))
            saved=json.loads((folder/'summary.json').read_text());folder=folder/saved['last_result']
        cases.append(dict(case_id=key,source=str(folder),source_sha256=sha256(folder/'trajectory.npz'),metadata_sha256=sha256(folder/'trajectory.json')))
    if sources is not None:
        for item in json.loads(Path(sources).read_text()):
            key=item['case_id'];folder=Path(item['source'])
            if Path(key).name!=key or key in ('.','..') or any(c['case_id']==key for c in cases):raise ValueError('Invalid or duplicate case ID')
            options={k:item[k] for k in ('settings','horizon_days','duration_bounds_days','transfer_bounds_days') if k in item}
            cases.append(dict(case_id=key,source=str(folder),source_sha256=sha256(folder/'trajectory.npz'),metadata_sha256=sha256(folder/'trajectory.json'),**options))
        if not cases:raise ValueError('Empty accepted IRT source manifest')
    plan=dict(cases=cases,settings=SETTINGS,release_factors=[[.5,1.5],[.5,2.]],changed_physical_parameters=['tof_days only'],
              source_archive=str(archive if sources is None else sources),scope='heliocentric physical PSI; no parking or capture spirals')
    if (root/'design.json').exists():
        if json.loads((root/'design.json').read_text())!=plan:raise ValueError('Design changed')
    else:write_json(root/'design.json',plan)
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--phase',choices=['primary','recover'],default='primary');p.add_argument('--workers',type=int,default=4)
    p.add_argument('--sources',help='JSON list of case_id/source accepted trajectory folders; defaults to coordinate_matrix_v1')
    a=p.parse_args();root=Path(a.output);root.mkdir(parents=True,exist_ok=True);cases=design(root,a.sources);rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(run_case,(case,str(root),a.phase)):case for case in cases}
        for f in as_completed(futures):
            case=futures[f]
            try:r=f.result()
            except Exception as exc:r=dict(case_id=case['case_id'],status='worker_error',error=str(exc))
            rows.append(r);write_json(root/(a.phase+'_results.json'),sorted(rows,key=lambda r:r['case_id']))
            print(r['case_id'],r['status'],r.get('last_stage'),r.get('fuel_kg'),flush=True)

if __name__=='__main__':main()


