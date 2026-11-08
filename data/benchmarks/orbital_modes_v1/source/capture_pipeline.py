"""Coupled heliocentric transfer and planet-centered capture, shared controller."""
from dataclasses import replace,asdict
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.optimize import brentq
from .data import Trajectory,write_json,DAY_S,sha256
from .problem import Mission
from .ephemerides import Ephemerides
from .planetary_capture import CaptureOrbit,backward_capture,orient_capture,correct_interface,forward_capture,elements


def verify_capture_mission(folder):
    from .contract import audit_configuration
    from .bounded import verify_bounded
    from .kiam_verification import verify_kiam_psi
    folder=Path(folder);mission=Mission.load(folder/'mission.json')
    outer=Trajectory.load(folder/'outer');inner=Trajectory.load(folder/'capture');joint=Trajectory.load(folder/'final')
    om=Mission(**outer.metadata['mission']);req=json.loads((folder/'outer_request.json').read_text())
    # A resolved offset is the only physical difference from the requested mission.
    expected=replace(mission,arrival_offset_state_si=om.arrival_offset_state_si)
    if om.to_dict()!=expected.to_dict():raise ValueError('Capture outer segment changed the requested mission')
    audit=audit_configuration(outer,expected,req,require_final=True)
    orbit=CaptureOrbit(**{k:mission.capture[k] for k in CaptureOrbit.__dataclass_fields__})
    planet=Ephemerides().state(mission.target,om.arrival_jd)
    rjoin=planet[:3]+inner.arrays['r_m'][0];vjoin=planet[3:]+inner.arrays['v_m_s'][0]
    dr=float(np.linalg.norm(rjoin-outer.arrays['r_m'][-1]));dv=float(np.linalg.norm(vjoin-outer.arrays['v_m_s'][-1]))
    dm=abs(float(inner.arrays['mass_kg'][0]-outer.arrays['mass_kg'][-1]))
    meta=inner.metadata
    final=elements(np.r_[inner.arrays['r_m'][-1],inner.arrays['v_m_s'][-1]],orbit.mu_m3_s2)
    rp=orbit.planet_radius_m+orbit.periapsis_altitude_m;ra=orbit.planet_radius_m+orbit.apoapsis_altitude_m
    orbit_error=max(abs(final['periapsis_radius_m']-rp),abs(final['apoapsis_radius_m']-ra))
    elapsed=outer.arrays['t_s'][-1]+inner.arrays['t_s'][-1]
    fuel=float(mission.mass_kg-joint.arrays['mass_kg'][-1])
    fuel_outer=float(mission.mass_kg-outer.arrays['mass_kg'][-1])
    fuel_capture=float(inner.arrays['mass_kg'][0]-inner.arrays['mass_kg'][-1])
    balance=abs(fuel-fuel_outer-fuel_capture)
    q=mission.spacecraft['thrust_N']/mission.spacecraft['exhaust_velocity_m_s']
    capture_balance=abs(fuel_capture-q*(meta['duration_s']-meta['burn_start_s']))
    expected_r=np.vstack([outer.arrays['r_m'],(Ephemerides().state(mission.target,om.arrival_jd+inner.arrays['t_s'][1:]/DAY_S)[:,:3]+inner.arrays['r_m'][1:])])
    composition_r=float(np.linalg.norm(joint.arrays['r_m']-expected_r,axis=1).max())
    ep=Ephemerides().state(mission.target,om.arrival_jd+inner.arrays['t_s'][1:]/DAY_S)
    expected_v=np.vstack([outer.arrays['v_m_s'],ep[:,3:]+inner.arrays['v_m_s'][1:]])
    composition_v=float(np.linalg.norm(joint.arrays['v_m_s']-expected_v,axis=1).max())
    composition_m=float(np.max(np.abs(joint.arrays['mass_kg']-np.r_[outer.arrays['mass_kg'],inner.arrays['mass_kg'][1:]])))
    composition_t=float(np.max(np.abs(joint.arrays['t_s']-np.r_[outer.arrays['t_s'],outer.arrays['t_s'][-1]+inner.arrays['t_s'][1:]])))
    composition_thrust=float(np.max(np.abs(joint.arrays['thrust_N']-np.r_[outer.arrays['thrust_N'],inner.arrays['thrust_N'][1:]])))
    links=(meta['source_outer_arrays_sha256']==outer.metadata['arrays_sha256']
           and joint.metadata['source_outer_arrays_sha256']==outer.metadata['arrays_sha256']
           and joint.metadata['source_capture_arrays_sha256']==inner.metadata['arrays_sha256'])
    hardware=(meta['mission']==mission.to_dict() and meta['orbit']==asdict(orbit)
              and joint.metadata['mission']==mission.to_dict()
              and meta['center']==mission.target and meta['epoch_jd']==mission.arrival_jd
              and joint.metadata['center']=='Sun' and joint.metadata['epoch_jd']==mission.launch_jd
              and all(x.metadata['frame']=='ECLIPJ2000' and x.metadata['time_scale']=='TDB' for x in (inner,joint))
              and np.array_equal(inner.arrays['thrust_N'],np.where(inner.arrays['t_s']>=meta['burn_start_s'],mission.spacecraft['thrust_N'],0.)))
    # Reject corrupted composition before spending time in numerical solvers.
    if not (composition_r<.001 and composition_v<1e-8 and composition_m<1e-6 and composition_t<1e-6
            and composition_thrust<1e-12 and links and hardware):
        return dict(passed=False,kind='patched_planet_capture',reason='Composition, source link or hardware mismatch')
    outer_check=verify_bounded(outer);vendor=verify_kiam_psi(outer)
    replay=forward_capture(orbit,np.r_[inner.arrays['r_m'][0],inner.arrays['v_m_s'][0]],inner.arrays['mass_kg'][0],
                           mission.spacecraft['thrust_N'],mission.spacecraft['exhaust_velocity_m_s'],
                           meta['burn_start_s'],meta['duration_s'],sample_times=inner.arrays['t_s'])
    # Replayed samples include the stored mesh, so exact lookup avoids resampling error.
    indices=np.searchsorted(replay['t_s'],inner.arrays['t_s'])
    replay_r=float(np.linalg.norm(replay['relative_state_si'][indices,:3]-inner.arrays['r_m'],axis=1).max())
    replay_v=float(np.linalg.norm(replay['relative_state_si'][indices,3:]-inner.arrays['v_m_s'],axis=1).max())
    passed=(audit['passed'] and outer_check['passed'] and vendor['passed'] and dr<.001 and dv<1e-8 and dm<1e-6
            and orbit_error<1000. and replay_r<100. and replay_v<.01 and balance<1e-6 and capture_balance<1e-6
            and composition_r<.001 and composition_v<1e-8 and composition_m<1e-6 and composition_t<1e-6
            and composition_thrust<1e-12 and links and hardware and joint.arrays['t_s'][-1]==elapsed
            and np.min(joint.arrays['mass_kg'])>=mission.spacecraft['dry_mass_kg']-1e-6
            and replay['minimum_radius_m']>=orbit.planet_radius_m+orbit.periapsis_altitude_m-1000.)
    return dict(passed=bool(passed),kind='patched_planet_capture',join_position_error_m=dr,join_velocity_error_m_s=dv,
                join_mass_error_kg=dm,orbit_element_error_m=orbit_error,periapsis_altitude_m=final['periapsis_radius_m']-orbit.planet_radius_m,
                apoapsis_altitude_m=final['apoapsis_radius_m']-orbit.planet_radius_m,capture_replay_position_error_m=replay_r,
                capture_replay_velocity_error_m_s=replay_v,total_fuel_kg=fuel,interplanetary_fuel_kg=fuel_outer,capture_fuel_kg=fuel_capture,
                composition_position_error_m=composition_r,composition_velocity_error_m_s=composition_v,
                composition_mass_error_kg=composition_m,composition_time_error_s=composition_t,source_links_passed=links,hardware_passed=hardware,
                mass_balance_error_kg=balance,capture_mass_flow_error_kg=capture_balance,total_duration_days=elapsed/DAY_S,
                final_mass_kg=float(joint.arrays['mass_kg'][-1]),outer_verification=outer_check,kiam_outer_verification=vendor,
                scope='State/velocity/mass-continuous patched central fields; prescribed legacy transverse capture law; no joint optimality or N-body claim')


def run_capture_pipeline(mission,output,resume=False):
    output=Path(output);mission.validate()
    checkpoint=None
    if resume and (output/'mission.json').exists():
        if Mission.load(output/'mission.json').to_dict()!=mission.to_dict():raise ValueError('Capture resume changes the mission')
        if (output/'summary.json').exists() and json.loads((output/'summary.json').read_text()).get('status')=='completed':
            check=verify_capture_mission(output)
            if not check['passed']:raise ValueError('Saved planetary capture failed replay')
            return Trajectory.load(output/'final'),json.loads((output/'summary.json').read_text())
        if (output/'outer/trajectory.json').exists() and (output/'coupling.json').exists():
            checkpoint=json.loads((output/'coupling.json').read_text())
            matches=[x for x in checkpoint['history'] if abs(x['mass_residual_kg'])<1e-5]
            if not matches:raise ValueError('No mass-consistent checkpoint to resume')
            saved_outer=Trajectory.load(output/'outer')
            matches=[x for x in matches if Trajectory.load(Path(x['folder'])/'outer').metadata['arrays_sha256']==saved_outer.metadata['arrays_sha256']]
            if not matches:raise ValueError('Mass checkpoint does not identify the saved outer segment')
            checkpoint=matches[-1]
        else:raise ValueError('Incomplete capture has no matched interface checkpoint')
    output.mkdir(parents=True,exist_ok=bool(checkpoint))
    write_json(output/'mission.json',mission.to_dict())
    summary=dict(case_id=mission.case_id,status='running',phase='planet_capture',capture_phase='interplanetary_seed',
                 completion_scope='planetary_orbit',capture_included=True)
    write_json(output/'summary.json',summary)
    from .runtime import runtime_environment
    write_json(output/'capture_runtime.json',runtime_environment())
    orbit=CaptureOrbit(**{k:mission.capture[k] for k in CaptureOrbit.__dataclass_fields__})
    spacecraft=mission.spacecraft;F=spacecraft['thrust_N'];c=spacecraft['exhaust_velocity_m_s']
    from .runner import run_pipeline
    if mission.solver.get('capture_seed_path'):
        seed=Trajectory.load(mission.solver['capture_seed_path'])
    else:
        seed,seed_summary=run_pipeline(replace(mission,capture=None,arrival_offset_state_si=None),output/'seed_pipeline')
        if seed_summary['status']!='completed':
            summary.update(status='partial',stop_kind='capture_seed_unavailable',error='Heliocentric seed did not complete')
            write_json(output/'summary.json',summary);return seed,summary
    planet=Ephemerides().state(mission.target,mission.arrival_jd)
    evaluations={};history=[];latest=seed;started=perf_counter()
    def evaluate(mf):
        nonlocal latest
        mf=float(mf)
        if mf in evaluations:return evaluations[mf]
        if perf_counter()-started>float(mission.solver.get('capture_budget_s',300)):raise TimeoutError('Coupled capture budget reached')
        nominal=orient_capture(backward_capture(orbit,mf,F,c),planet)
        resolved=replace(mission,arrival_offset_state_si=nominal['relative_state_si'][0].tolist())
        summary['capture_phase']='interplanetary_interface';write_json(output/'summary.json',summary)
        outer,request=correct_interface(latest,resolved,budget_s=float(mission.solver.get('capture_match_attempt_s',60)))
        latest=outer
        folder=output/f'evaluation_{len(history):03d}';folder.mkdir()
        outer.save(folder/'outer');write_json(folder/'request.json',request)
        residual=float(outer.arrays['mass_kg'][-1]-nominal['entry_mass_kg'])
        event=dict(final_mass_guess_kg=mf,mass_residual_kg=residual,outer_entry_mass_kg=float(outer.arrays['mass_kg'][-1]),
                   spiral_entry_mass_kg=nominal['entry_mass_kg'],duration_days=float(nominal['duration_s']/DAY_S),folder=str(folder))
        history.append(event);write_json(output/'coupling.json',dict(status='matching',history=history))
        summary.update(capture_phase='mass_consistency',last_verified_artifact=str(folder/'outer'));write_json(output/'summary.json',summary)
        evaluations[mf]=(residual,outer,request,nominal)
        print('capture mass coupling',mf,residual,flush=True)
        return evaluations[mf]
    try:
        if checkpoint:
            history=json.loads((output/'coupling.json').read_text())['history']
            mf=checkpoint['final_mass_guess_kg'];residual=checkpoint['mass_residual_kg']
            outer=Trajectory.load(output/'outer');request=json.loads((output/'outer_request.json').read_text())
            nominal=orient_capture(backward_capture(orbit,mf,F,c),planet)
            from .contract import audit_configuration
            audit_configuration(outer,replace(mission,arrival_offset_state_si=nominal['relative_state_si'][0].tolist()),request,require_final=True)
            latest=outer
        else:
            lo=float(spacecraft['dry_mass_kg']);hi=float(seed.arrays['mass_kg'][-1])
            mf=brentq(lambda x:evaluate(x)[0],lo,hi,xtol=1e-7,maxiter=12)
            residual,outer,request,nominal=evaluate(mf)
        if abs(residual)>1e-5:raise RuntimeError('Capture mass consistency did not converge')
        if not checkpoint:
            outer.save(output/'outer');write_json(output/'outer_request.json',request)
        outer=Trajectory.load(output/'outer')
        write_json(output/'coupling.json',dict(status='mass_matched',mass_residual_kg=residual,history=history))
        summary['capture_phase']='planetary_propagation';write_json(output/'summary.json',summary)
        actual_state=np.r_[outer.arrays['r_m'][-1],outer.arrays['v_m_s'][-1]]-planet
        physical=forward_capture(orbit,actual_state,float(outer.arrays['mass_kg'][-1]),F,c,
                                 nominal['burn_start_s'],nominal['duration_s'],sample_times=nominal['t_s'])
        inner_meta=dict(case_id=mission.case_id,epoch_jd=mission.arrival_jd,time_scale='TDB',frame='ECLIPJ2000',center=mission.target,
                        stage='planet_capture',status='propagated',model='planet-centered transverse braking, constant F,c and variable mass',
                        title='Скрутка у '+mission.target,mission=mission.to_dict(),orbit=asdict(orbit),
                        burn_start_s=float(nominal['burn_start_s']),duration_s=float(nominal['duration_s']),
                        source_outer_arrays_sha256=outer.metadata['arrays_sha256'])
        inner=Trajectory(inner_meta,dict(t_s=physical['t_s'],r_m=physical['relative_state_si'][:,:3],v_m_s=physical['relative_state_si'][:,3:],
                                         mass_kg=physical['mass_kg'],thrust_N=physical['thrust_N'],active=physical['thrust_N']>0))
        # Preserve unsuccessful downstream artifacts when regenerating from
        # a verified mass-matched checkpoint.
        for name in ('capture','final'):
            if (output/name).exists():
                index=1
                while (output/f'{name}_previous_{index:03d}').exists():index+=1
                (output/name).rename(output/f'{name}_previous_{index:03d}')
        inner.save(output/'capture')
        inner=Trajectory.load(output/'capture')
        ep=Ephemerides().state(mission.target,mission.arrival_jd+inner.arrays['t_s'][1:]/DAY_S)
        arrays=dict(t_s=np.r_[outer.arrays['t_s'],outer.arrays['t_s'][-1]+inner.arrays['t_s'][1:]],
                    r_m=np.vstack([outer.arrays['r_m'],ep[:,:3]+inner.arrays['r_m'][1:]]),
                    v_m_s=np.vstack([outer.arrays['v_m_s'],ep[:,3:]+inner.arrays['v_m_s'][1:]]),
                    mass_kg=np.r_[outer.arrays['mass_kg'],inner.arrays['mass_kg'][1:]],
                    thrust_N=np.r_[outer.arrays['thrust_N'],inner.arrays['thrust_N'][1:]],
                    active=np.r_[outer.arrays['active'],inner.arrays['active'][1:]])
        meta=dict(case_id=mission.case_id,epoch_jd=mission.launch_jd,time_scale='TDB',frame='ECLIPJ2000',center='Sun',stage='capture_mission',
                  status='pending_verification',model='patched heliocentric and planet-centered central fields',mission=mission.to_dict(),
                  title='Земля → '+mission.target+': перелёт и скрутка',join_time_s=mission.tof_days*DAY_S,
                  capture_included=True,completion_scope='planetary_orbit')
        meta.update(source_outer_arrays_sha256=outer.metadata['arrays_sha256'],source_capture_arrays_sha256=inner.metadata['arrays_sha256'])
        meta['overlays']=outer.metadata.get('overlays',[])
        for overlay in meta['overlays']:arrays[overlay['array']]=outer.arrays[overlay['array']].copy()
        meta['markers']=[dict(label=mission.departure+', старт',r_m=outer.arrays['r_m'][0].tolist()),
                         dict(label='Вход в сферу '+mission.target,r_m=outer.arrays['r_m'][-1].tolist(),hollow=True),
                         dict(label='Конечная орбита у '+mission.target,r_m=arrays['r_m'][-1].tolist(),color='#df1111',role='target')]
        joint=Trajectory(meta,arrays);joint.save(output/'final')
        summary['capture_phase']='stitch_verification';write_json(output/'summary.json',summary)
        check=verify_capture_mission(output)
        if not check['passed']:raise RuntimeError('Capture stitch or final orbit failed verification: '+str(check))
        write_json(output/'verification.json',check)
        joint=Trajectory.load(output/'final')
        joint.metadata.update(status='verified_capture',verification=check)
        write_json(output/'final/trajectory.json',joint.metadata)
        inner.metadata.update(status='verified_capture')
        write_json(output/'capture/trajectory.json',inner.metadata)
        summary.update(status='completed',phase='final',verification=check,final_mass_kg=check['final_mass_kg'],
                       arrays_sha256=Trajectory.load(output/'final').metadata['arrays_sha256'])
        write_json(output/'summary.json',summary)
        write_json(output/'coupling.json',dict(status='mass_matched',mass_residual_kg=residual,history=history))
        from .visualization import render
        render(outer,output/'outer_plots');render(inner,output/'capture_plots');render(joint,output/'plots')
        return Trajectory.load(output/'final'),summary
    except (ValueError,RuntimeError,TimeoutError) as exc:
        phase=summary['capture_phase']
        kind=('capture_time_budget' if isinstance(exc,TimeoutError) else
              'capture_verification_failed' if phase=='stitch_verification' else
              'capture_propagation_failed' if phase=='planetary_propagation' else 'capture_matching_failed')
        summary.update(status='partial',error=str(exc),stop_kind=kind)
        write_json(output/'summary.json',summary)
        return latest,summary
