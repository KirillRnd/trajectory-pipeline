"""Outer duration optimization with full re-stitching of every trial mission."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.optimize import minimize_scalar
from .data import Trajectory,write_json,sha256
from .problem import Mission
from .contract import specification
from .coordinate_matrix import timed_call


def verify_selection(folder,verify):
    folder=Path(folder);file=folder/'time_selection.json'
    if not file.exists():return None
    selected=json.loads(file.read_text());child=folder/selected['artifact']
    requested=Mission.load(folder/'mission.json');actual=Mission.load(child/'mission.json')
    expected=replace(requested,tof_days=actual.tof_days,time_policy=None)
    if specification(expected)!=specification(actual):raise ValueError('Composed time selection changes physical request')
    lo,hi=requested.time_policy['bounds_days']
    if not lo<=actual.tof_days<=hi:raise ValueError('Composed time outside requested bounds')
    if sha256(child/'final/trajectory.npz')!=selected['arrays_sha256']:raise ValueError('Selected mission changed')
    result=verify(child)
    result['duration_search']=selected
    return result


def run_composed_time(mission,output,resume=False):
    if mission.orbital_maneuvers is not None:
        from .orbital_pipeline import run_orbital_pipeline as run,verify_orbital_mission as verify
    elif mission.parking_departure is not None:
        from .launch_pipeline import run_launch_pipeline as run,verify_launch_mission as verify
    elif mission.capture is not None:
        from .capture_pipeline import run_capture_pipeline as run,verify_capture_mission as verify
    else:raise ValueError('Composed time requires orbital maneuvers')
    root=Path(output);root.mkdir(parents=True,exist_ok=resume)
    saved=root/'mission.json'
    if saved.exists() and Mission.load(saved).to_dict()!=mission.to_dict():raise ValueError('Composed time resume changed request')
    write_json(saved,mission.to_dict())
    if (root/'time_selection.json').exists():
        check=verify(root)
        if not check['passed']:raise ValueError('Selected mission failed replay')
        return Trajectory.load(root/'final'),json.loads((root/'summary.json').read_text())
    history=json.loads((root/'time_trials.json').read_text()) if (root/'time_trials.json').exists() else []
    lo,hi=mission.time_policy['bounds_days'];accepted=[]
    for event in history:
        if event.get('accepted') and verify(root/event['artifact'])['passed']:accepted.append(event)
    deadline=perf_counter()+float(mission.solver.get('orbital_time_budget_s',600))
    budget=float(mission.solver.get('orbital_time_trial_s',240))
    def evaluate(duration):
        duration=float(duration)
        for event in history:
            if abs(event['tof_days']-duration)<1e-8:return event.get('fuel_kg',1e12)
        if perf_counter()>=deadline:raise TimeoutError('Composed duration budget reached')
        folder=root/f'time_trial_{len(history):03d}'
        while folder.exists():folder=folder.with_name(folder.name+'_retry')
        settings=dict(mission.solver,irt_entry='fixed_time');settings.pop('iltt_resolved',None)
        if accepted and mission.orbital_maneuvers is not None:
            nearest=min(accepted,key=lambda r:abs(r['tof_days']-duration))
            seed=deepcopy(Trajectory.load(root/nearest['artifact']/'outer'))
            ratio=duration/seed.metadata['mission']['tof_days']
            seed.arrays['t_s']*=ratio
            if 'switch_times_s' in seed.metadata:seed.metadata['switch_times_s']=(np.asarray(seed.metadata['switch_times_s'])*ratio).tolist()
            seed.metadata['mission']['tof_days']=duration;seed.metadata['status']='unverified_retimed_guess'
            seed_folder=root/(folder.name+'_seed');seed.save(seed_folder)
            settings['orbital_seed_path']=str(seed_folder.resolve())
        trial=replace(mission,tof_days=duration,time_policy=None,solver=settings)
        event=dict(tof_days=duration,artifact=folder.name,accepted=False)
        try:
            result,state=timed_call(min(budget,max(.01,deadline-perf_counter())),run,trial,folder)
            event['status']=state['status'];event['error']=state.get('error')
            if state['status']=='completed':
                check=verify(folder)
                if not check['passed']:raise ValueError('Re-stitched mission failed replay')
                event.update(accepted=True,fuel_kg=float(mission.mass_kg-result.arrays['mass_kg'][-1]),verification=check)
                accepted.append(event)
        except (ValueError,RuntimeError,TimeoutError) as exc:event['error']=str(exc)
        history.append(event);write_json(root/'time_trials.json',history)
        return event.get('fuel_kg',1e12)
    optimized=False;error=None
    try:
        evaluate(mission.tof_days)
        # Probe nearby real durations before distant endpoints; no synthetic BVP.
        span=hi-lo;evaluate(max(lo,mission.tof_days-.05*span));evaluate(min(hi,mission.tof_days+.05*span))
        opt=minimize_scalar(evaluate,bounds=(lo,hi),method='bounded',options=dict(maxiter=int(mission.solver.get('orbital_time_iterations',8)),xatol=.05))
        optimized=bool(opt.success)
    except TimeoutError as exc:error=str(exc)
    changed=[e for e in accepted if abs(e['tof_days']-mission.tof_days)>1e-7]
    summary=dict(case_id=mission.case_id,status='completed' if changed else 'partial',phase='orbital_time',
                 completion_scope='initial_orbit_to_final_orbit',duration_released=bool(changed),optimizer_success=optimized,
                 error=error,trials=len(history),time_reference='interplanetary duration; both local segments re-stitched')
    result=None
    if changed:
        best=min(accepted,key=lambda e:e['fuel_kg'])
        result=Trajectory.load(root/best['artifact']/'final');result.save(root/'final')
        selection=dict(artifact=best['artifact'],tof_days=best['tof_days'],bounds_days=[lo,hi],
                       arrays_sha256=sha256(root/best['artifact']/'final/trajectory.npz'),optimizer_success=optimized)
        write_json(root/'time_selection.json',selection)
        summary.update(last_result='final',selected=selection,verification=verify(root))
    elif accepted:summary['physical_parent']=min(accepted,key=lambda e:e['fuel_kg'])['artifact']
    write_json(root/'summary.json',summary);return result,summary
