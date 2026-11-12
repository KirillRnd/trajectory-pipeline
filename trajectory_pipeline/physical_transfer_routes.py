"""Independent physical R transfers and a broad early-time route for residual cases."""
import argparse,json
from copy import deepcopy
from pathlib import Path
from dataclasses import replace,asdict
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .data import Trajectory,Scales,write_json,sha256
from .problem import Mission
from .accepted_irt_routes import physical,SETTINGS,checked_checkpoint,save_version,verify_stage
from .contract import audit_configuration,make_request
from .date_sweep import _seed,_date_context
from .bangbang import solve_bangbang
from .bounded_model import BoundedModel,origin_and_boundary
from .r_transform import orbital_frame
from .free_time import release_duration
from .intermediate_time import release_intermediate_duration,continue_physical_model
from .coordinate_matrix import timed_call


def compatible(a,b):
    fields=('departure','target','center','mode','mass_kg','spacecraft','departure_mode','vinf_max_m_s','vinf_vector_m_s','orbit_sources')
    return all(getattr(a,k)==getattr(b,k) for k in fields)


def exact_time_seed(parent):
    """Infer arc topology from a smooth control; this remains an unverified guess."""
    guess=deepcopy(parent)
    if 'switch_times_s' not in guess.metadata:
        times=np.asarray(guess.arrays['t_s']);throttle=np.asarray(guess.arrays['throttle'])
        if times.shape!=throttle.shape or len(times)<2:
            raise ValueError('Missing sampled control for exact-time initialization')
        changes=np.flatnonzero(np.diff((throttle>.5).astype(int)))
        switches=[float(times[i]+(.5-throttle[i])/(throttle[i+1]-throttle[i])*(times[i+1]-times[i])) for i in changes]
        if np.any(np.diff(np.r_[times[0],switches,times[-1]])<=0):
            raise ValueError('Degenerate initial switching topology')
        guess.metadata.update(switch_times_s=switches,initial_throttle=float(throttle[0]>.5),status='unverified_arc_guess')
    return guess


def worker(task):
    case,rootstr,reference=task;root=Path(rootstr)/case['case_id'];dest=root/'transfer.json'
    if dest.exists():
        cached=json.loads(dest.read_text())
        if cached['status']=='completed':
            actual=Trajectory.load(cached['artifact']);original=Mission(**Trajectory.load(case['source']).metadata['mission'])
            physical(actual,replace(original,tof_days=actual.metadata['mission']['tof_days']))
            return cached
    attempts=sorted(root.glob('transfer_attempt_*.json'))
    if len(attempts)>=3:
        return json.loads(dest.read_text()) if dest.exists() else dict(case_id=case['case_id'],status='partial',phase='transfer',error='Three transfer attempts exhausted')
    write_json(root/f'transfer_attempt_{len(attempts)+1:02d}.json',dict(source=case['source'],source_sha256=sha256(Path(case['source'])/'trajectory.npz'),reference=reference))
    seed=Trajectory.load(case['source']);original=Mission(**seed.metadata['mission'])
    settings=dict(SETTINGS,**case.get('settings',{}))
    seed.metadata['mission']['solver'].update(settings)
    bounds=case.get('transfer_bounds_days',case.get('duration_bounds_days',[.5*original.tof_days,max(2*original.tof_days,1095.75)]))
    bounds=[bounds[0],min(bounds[1],case.get('horizon_days',float('inf')))]
    if not 0<bounds[0]<bounds[1]:raise ValueError('Empty physical recovery time interval')
    events=[];summary=dict(case_id=case['case_id'],status='partial',phase='transfer',bounds_days=bounds)
    def accept(result,label):
        check=physical(result);actual=Mission(**result.metadata['mission'])
        expected=replace(original,tof_days=actual.tof_days)
        audit_configuration(result,expected,make_request(expected),require_final=True)
        if not bounds[0]<=actual.tof_days<=bounds[1]:raise ValueError('Time outside declared recovery bounds')
        result.metadata.update(verification=check['verification'],kiam_verification=check['kiam_verification'])
        output=save_version(result,root/'transfer_physical');summary.update(status='completed',artifact=str(output),route=label,**check)
    # Independently correct exact arcs from the best already verified physical-
    # mass/thrust intermediate, trying the existing costate charts explicitly.
    eligible=[]
    for name in ('primary_last','coupled_checkpoint','after_release_checkpoint','early_continue_checkpoint','recover_last'):
        path=root/name
        if not (path/'trajectory.json').exists():continue
        parent=Trajectory.load(path);spec=parent.metadata.get('bounded_model')
        if not spec or not spec.get('variable_mass') or spec.get('beta')!=1:continue
        sc=Scales(**parent.metadata['scales']);m=Mission(**parent.metadata['mission'])
        force=spec['a_max']*sc.acceleration_m_s2*m.mass_kg
        if not np.isclose(force,m.spacecraft['thrust_N'],rtol=1e-8,atol=1e-12):continue
        eligible.append((spec['alpha'],parent,str(path)))
    if eligible:
        _,parent,parent_path=max(eligible,key=lambda row:row[0])
        sc=Scales(**parent.metadata['scales']);model=replace(BoundedModel(**parent.metadata['bounded_model']),alpha=1.)
        body,_=origin_and_boundary(parent,sc)
        for chart_name in ('cartesian','legacy','rtn'):
            event=dict(operation='exact_arcs_'+chart_name,parent=parent_path,alpha_seed=parent.metadata['bounded_model']['alpha'])
            try:
                frame=None if chart_name=='cartesian' else orbital_frame(body,chart_name)
                candidate=timed_call(35,solve_bangbang,parent,parent,model,perf_counter()+30,'psi',costate_frame=frame)
                accept(candidate,'exact physical arcs in '+chart_name+' costate coordinates');event['status']='completed'
            except Exception as exc:event.update(status='failed',error=str(exc))
            events.append(event)
            if summary['status']=='completed':break
        if summary['status']!='completed':
            event=dict(operation='exact_free_time',parent=parent_path,bounds_days=bounds)
            try:
                context=deepcopy(parent);context.metadata['bounded_model']=asdict(model)
                context.metadata['status']='unverified_physical_context'
                candidate=timed_call(95,release_duration,context,exact_time_seed(parent),bounds,perf_counter()+90)
                accept(candidate,'exact physical model + free duration from smooth parent');event['status']='completed'
            except Exception as exc:event.update(status='failed',error=str(exc))
            events.append(event)
    if summary['status']=='completed':
        summary['events']=events;write_json(dest,summary);return summary
    if reference:
        ref=Trajectory.load(reference);physical(ref);old=Mission(**ref.metadata['mission'])
        if not compatible(original,old):raise ValueError('Reference physical parameters differ')
        duration=float(np.clip(old.tof_days,bounds[0]+1e-6,bounds[1]-1e-6))
        mission=replace(original,tof_days=duration,solver=dict(original.solver,**settings))
        body,target,scale=mission.boundary();prior=Scales(**ref.metadata['scales'])
        guess,R=_seed(ref,np.asarray(ref.metadata['body_initial_state_si']),body,prior,scale)
        ratio=duration/old.tof_days;guess.arrays['t_s']*=ratio
        if 'switch_times_s' in guess.metadata:guess.metadata['switch_times_s']=(np.asarray(guess.metadata['switch_times_s'])*ratio).tolist()
        context,model=_date_context(mission,body,target,scale);context.metadata['bounded_model']=asdict(model)
        write_json(root/'transfer_seed.json',dict(reference=reference,reference_arrays_sha256=sha256(Path(reference)/'trajectory.npz'),R=R.tolist(),duration=duration,bounds_days=bounds))
        candidate=guess
        event=dict(operation='R_fixed',reference=reference,tof_days=duration)
        try:
            candidate=timed_call(40,solve_bangbang,context,guess,model,perf_counter()+35,'psi')
            accept(candidate,'independent R transfer, changed duration');event['status']='completed'
        except Exception as exc:event.update(status='failed',error=str(exc))
        events.append(event)
        if summary['status']!='completed':
            event=dict(operation='R_free',reference=reference)
            try:
                result=timed_call(100,release_duration,context,candidate,bounds,perf_counter()+90)
                accept(result,'independent R transfer + free duration');event['status']='completed'
            except Exception as exc:event.update(status='failed',error=str(exc))
            events.append(event)
    else:events.append(dict(operation='R_transfer',status='unavailable',reason='No accepted physical reference with the same target, mode and hardware'))
    if summary['status']!='completed':
        # Different starting model and a common wider time domain; no target-specific tuning.
        event=dict(operation='broad_early_time',bounds_days=bounds)
        try:
            from .stage_journal import stage
            def release(initial,out):
                value=timed_call(95,release_intermediate_duration,initial,bounds,perf_counter()+90,out)
                return value,dict(status='completed_stage')
            candidate,_=stage(root,'broad_time',seed,release,verify_stage,recover=checked_checkpoint)
            candidate.metadata['mission']['solver'].update(dict(settings,pipeline_pazov_alpha=.3,psi_mass_alpha=.3))
            def proceed(initial,out):
                if initial.metadata.get('stage')=='psi':
                    physical(initial);return initial,dict(status='completed',phase='final')
                return timed_call(480,continue_physical_model,initial,out)
            result,state=stage(root,'broad_continue',candidate,proceed,verify_stage,recover=checked_checkpoint)
            event.update(status=state['status'],details=state)
            summary['last_checkpoint']=str(save_version(result,root/'broad_last'))
            if state['status']=='completed':accept(result,'broad early duration -> coupled physical continuation')
        except Exception as exc:event.update(status='failed',error=str(exc))
        events.append(event)
    summary['events']=events;write_json(dest,summary);return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--workers',type=int,default=8)
    a=p.parse_args();root=Path(a.output);cases=json.loads((root/'design.json').read_text())['cases']
    refs=[];pending=[]
    for c in cases:
        candidates=[]
        for phase in ('primary','recover'):
            file=root/c['case_id']/(phase+'.json')
            if file.exists():
                r=json.loads(file.read_text())
                if r['status']=='completed':candidates.append(r)
        if candidates:
            best=min(candidates,key=lambda r:r['fuel_kg']);refs.append(best['artifact'])
        else:pending.append(c)
    missions={ref:Mission(**Trajectory.load(ref).metadata['mission']) for ref in refs};tasks=[];design=[]
    for c in pending:
        m=Mission(**Trajectory.load(c['source']).metadata['mission'])
        options=[ref for ref in refs if compatible(m,missions[ref])]
        ref=min(options,key=lambda r:abs(m.launch_jd-missions[r].launch_jd)) if options else None
        tasks.append((c,str(root),ref));design.append(dict(case_id=c['case_id'],reference=ref))
    write_json(root/'transfer_design.json',dict(rule='Snapshot nearest accepted reference per target/mode/hardware; independent transfers',cases=design))
    rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(worker,t):t[0]['case_id'] for t in tasks}
        for f in as_completed(futures):
            try:r=f.result()
            except Exception as exc:r=dict(case_id=futures[f],status='worker_error',error=str(exc))
            rows.append(r);write_json(root/'transfer_results.json',rows)
            print(r['case_id'],r['status'],r.get('fuel_kg'),flush=True)

if __name__=='__main__':main()

