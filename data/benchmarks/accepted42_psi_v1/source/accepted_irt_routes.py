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


def physical(result):
    m=Mission(**result.metadata['mission'])
    audit=audit_configuration(result,m,make_request(m),require_final=True)
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


def run_case(request):
    case,rootstr,phase=request;root=Path(rootstr)/case['case_id'];root.mkdir(parents=True,exist_ok=True)
    path=root/(phase+'.json')
    if path.exists():return json.loads(path.read_text())
    source=Trajectory.load(case['source']);original=Mission(**source.metadata['mission'])
    audit_configuration(source,original,make_request(original))
    if not verify_irt(source)['passed']:raise ValueError('Input IRT replay failed')
    source.metadata['mission']['solver'].update(SETTINGS)
    current=source;history=[];result=dict(case_id=case['case_id'],phase=phase,status='partial',source=case['source'])
    began=perf_counter()
    def log(event):
        history.append(event);write_json(root/(phase+'_progress.json'),dict(events=history))
    def operation(name,fn,budget):
        nonlocal current
        out=root/name;event=dict(operation=name,input_stage=current.metadata.get('stage'),input_days=current.metadata['mission']['tof_days'])
        try:
            current,state=timed_call(budget,fn,current,out)
            event.update(status=state['status'],stopped_phase=state.get('phase'),details=state)
        except Exception as exc:
            event.update(status='exception',error=type(exc).__name__+': '+str(exc))
            current=checked_checkpoint(out,current)
        current.save(root/(name+'_checkpoint'))
        current=Trajectory.load(root/(name+'_checkpoint'))
        event['checkpoint']=str(root/(name+'_checkpoint'));log(event)
        return event
    def accept(label):
        try:
            check=physical(current)
        except (ValueError,RuntimeError,KeyError) as exc:return False
        out=root/(phase+'_physical');current.metadata.update(verification=check['verification'],kiam_verification=check['kiam_verification'])
        current.save(out);result.update(status='completed',artifact=str(out),route=label,**check)
        return True
    def release(name,seed,factor):
        nonlocal current
        current=deepcopy(seed);t=original.tof_days;bounds=[.5*t,factor*t]
        event=dict(operation=name,bounds_days=bounds,input_days=current.metadata['mission']['tof_days'])
        try:
            verify_intermediate(current)
            current=timed_call(65,release_intermediate_duration,current,bounds,perf_counter()+60,root/name)
            event.update(status='completed_stage',output_days=current.metadata['mission']['tof_days'],details=current.metadata.get('intermediate_time'))
        except Exception as exc:event.update(status='failed',error=type(exc).__name__+': '+str(exc))
        current.save(root/(name+'_checkpoint'));current=Trajectory.load(root/(name+'_checkpoint'));event['checkpoint']=str(root/(name+'_checkpoint'));log(event)
        return event['status']=='completed_stage'
    try:
        if phase=='primary':
            operation('departure',lambda s,o:run_departure(s,o),65)
            departure_ready=current.metadata.get('departure',{}).get('parameter',0)>=1-1e-10
            if departure_ready:
                operation('pazov',lambda s,o:run_pazov(s,o,target_alpha=.5),145)
                if current.metadata.get('stage') in ('pazov','pazov_limit'):
                    operation('psi',lambda s,o:run_psi(s,o),420)
            accept('standard: departure -> Pazov(.5) -> mass -> thrust -> fuel')
        elif phase=='recover':
            previous=json.loads((root/'primary.json').read_text())
            if previous['status']=='completed':return dict(case_id=case['case_id'],phase=phase,status='skipped_physical_parent')
            current=Trajectory.load(previous['last_checkpoint'])
            current.metadata['mission']['solver'].update(SETTINGS)
            try:verify_intermediate(current)
            except ValueError:
                # An exact but unaccepted endpoint must not erase the smooth parent.
                candidates=[root/'pazov_checkpoint',root/'departure_checkpoint']
                current=next((Trajectory.load(p) for p in candidates if (p/'trajectory.json').exists()),source)
            operation('coupled',continue_physical_model,420)
            if not accept('alternative: coupled mass/thrust'):
                if release('release_intermediate',current,1.5):
                    operation('after_release',continue_physical_model,420)
                    accept('intermediate duration -> coupled mass/thrust -> fuel')
            if result['status']!='completed':
                # A second path from an earlier model, not repetition at a stalled point.
                parent=Trajectory.load(root/'departure_checkpoint') if (root/'departure_checkpoint/trajectory.json').exists() else source
                parent.metadata['mission']['solver'].update(SETTINGS,pipeline_pazov_alpha=.3,psi_mass_alpha=.3)
                release('release_early',parent,2.)
                operation('early_continue',continue_physical_model,420)
                accept('early duration -> Pazov(.3) -> coupled mass/thrust -> fuel')
        else:raise ValueError('Unknown phase')
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        (root/(phase+'_error.log')).write_text(traceback.format_exc())
    checkpoint=root/(phase+'_last');current.save(checkpoint)
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
            cases.append(dict(case_id=key,source=str(folder),source_sha256=sha256(folder/'trajectory.npz'),metadata_sha256=sha256(folder/'trajectory.json')))
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


