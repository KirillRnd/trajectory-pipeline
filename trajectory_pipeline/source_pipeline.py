"""Explicit early-source -> physical-source boundary reconciliation in solve."""
from pathlib import Path
from dataclasses import replace
import json
from .data import Trajectory,write_json,sha256
from .problem import Mission
from .contract import audit_configuration,make_request
from .verification import verify_irt


def physical_sources(mission):
    return mission.solver.get('physical_orbit_sources',{b.lower():{'kind':'ephemerides'} for b in (mission.departure,mission.target)})


def needs_source_transition(mission):
    return bool(mission.orbit_sources and any(s.get('kind')=='kepler' for s in mission.orbit_sources.values())
                and physical_sources(mission)!=mission.orbit_sources)


def run_source_pipeline(mission,output,*,resume=False,release_time=False,time_bounds_days=None):
    from .runner import run_irt,run_pipeline
    from .orbit_transition import reconcile_irt
    root=Path(output);root.mkdir(parents=True,exist_ok=resume)
    request=dict(mission=mission.to_dict(),release_time=release_time,time_bounds_days=time_bounds_days)
    path=root/'source_request.json'
    if path.exists() and json.loads(path.read_text())!=request:raise ValueError('Source pipeline resume changes request')
    write_json(path,request)
    summary=dict(case_id=mission.case_id,status='partial',phase='irt',stages={},completion_scope='heliocentric_segment')
    def record():write_json(root/'summary.json',summary)
    early_mission=replace(mission,orbital_maneuvers=None,mass_reference=None,capture=None,parking_departure=None,
                          departure_offset_state_si=None,arrival_offset_state_si=None,time_policy=None)
    early=root/'early_irt';saved=early/'summary.json'
    state=json.loads(saved.read_text()) if saved.exists() else {}
    if state.get('status')!='completed_stage':state=run_irt(early_mission,early,resume=early.exists())
    summary['stages']['irt']=state;record()
    if state.get('status')!='completed_stage':return None,summary
    source=Trajectory.load(early/state['last_result'])
    if not verify_irt(source)['passed']:raise ValueError('Early IRT replay failed')
    early_expected=replace(early_mission,tof_days=source.metadata['mission']['tof_days'])
    audit_configuration(source,early_expected,make_request(early_expected))
    sources=physical_sources(mission);resolved=root/'resolved_irt';manifest=root/'transition.json'
    identity=dict(source_sha256=sha256(early/state['last_result']/'trajectory.npz'),sources=sources)
    if manifest.exists() and json.loads(manifest.read_text())!=identity:raise ValueError('Source transition input changed')
    # Bind input before committing the result, so a crash between result and
    # receipt does not turn a valid saved reconciliation into an orphan.
    write_json(manifest,identity)
    if resolved.exists():
        result=Trajectory.load(resolved)
    else:
        attempts=sorted(root.glob('transition_attempt_*'))
        if len(attempts)>=3:
            summary.update(phase='orbit_source_transition',error='Three source-transition attempts exhausted; preserve diagnostics and change route explicitly')
            record();return source,summary
        folder=root/f'transition_attempt_{len(attempts)+1:02d}'
        result,state=reconcile_irt(source,sources,folder,coordinates=['costates','iltt','costates'])
        summary['stages']['orbit_source_transition']=state;summary['phase']='orbit_source_transition';record()
        if state['status']!='completed_stage':return source,summary
        result.save(resolved);write_json(manifest,identity)
    actual=Mission(**result.metadata['mission'])
    expected=replace(early_mission,tof_days=actual.tof_days,orbit_sources=sources,time_policy=None)
    audit_configuration(result,expected,make_request(expected))
    if not verify_irt(result)['passed']:raise ValueError('Reconciled IRT replay failed')
    settings=dict(actual.solver,irt_entry='fixed_time',irt_artifact=str(resolved.resolve()))
    settings.pop('physical_orbit_sources',None);settings.pop('iltt_resolved',None);settings.pop('irt_date_fallback',None)
    physical=replace(mission,tof_days=actual.tof_days,orbit_sources=sources,solver=settings)
    child=root/'physical'
    final,child_state=run_pipeline(physical,child,resume=child.exists(),release_time=release_time,time_bounds_days=time_bounds_days)
    summary['stages']['physical']=child_state
    summary.update(status=child_state['status'],phase=child_state['phase'],physical_sources=sources,
                   physical_artifact=str(child/'final') if child_state['status']=='completed' else None)
    if child_state['status']=='completed':
        if physical.orbital_maneuvers is not None:
            from .orbital_pipeline import verify_orbital_mission
            if not verify_orbital_mission(child)['passed']:raise ValueError('Physical orbital replay failed')
        elif physical.capture is not None or physical.parking_departure is not None:
            from .capture_pipeline import verify_capture_mission
            from .launch_pipeline import verify_launch_mission
            check=verify_launch_mission(child) if physical.parking_departure is not None else verify_capture_mission(child)
            if not check['passed']:raise ValueError('Physical local-maneuver replay failed')
        else:
            audit_configuration(final,replace(physical,tof_days=final.metadata['mission']['tof_days']),make_request(replace(physical,tof_days=final.metadata['mission']['tof_days'])),require_final=True)
        summary['completion_scope']=child_state.get('completion_scope','heliocentric_segment')
        if not (root/'final').exists():final.save(root/'final')
        summary['last_result']='final'
    record();return final,summary
