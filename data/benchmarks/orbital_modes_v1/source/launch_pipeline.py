"""Couple circular parking-orbit injection to the finite outer boundary."""
from dataclasses import replace,asdict
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from .data import Trajectory,write_json,DAY_S
from .problem import Mission
from .ephemerides import Ephemerides
from .parking_departure import ParkingDeparture,outgoing_hyperbola,verify_outgoing


def verify_launch_mission(folder):
    from .contract import audit_configuration
    from .bounded import verify_bounded
    from .capture_pipeline import verify_capture_mission
    folder=Path(folder);mission=Mission.load(folder/'mission.json')
    summary=json.loads((folder/'summary.json').read_text())
    downstream=folder/summary['downstream_folder']
    if mission.capture:
        check=verify_capture_mission(downstream);outer=Trajectory.load(downstream/'outer')
    else:
        outer=Trajectory.load(downstream/'outer');check=verify_bounded(outer)
    om=Mission(**outer.metadata['mission'])
    expected=replace(mission,departure_offset_state_si=om.departure_offset_state_si,arrival_offset_state_si=om.arrival_offset_state_si,solver=om.solver)
    if expected.to_dict()!=om.to_dict():raise ValueError('Launch downstream mission changed requested physics')
    req=json.loads((downstream/('outer_request.json' if mission.capture else 'request.json')).read_text())
    audit_configuration(outer,expected,req,require_final=True)
    launch=Trajectory.load(folder/'launch');joint=Trajectory.load(folder/'final')
    planet=Ephemerides().state(mission.departure,mission.launch_jd)
    spec=ParkingDeparture(**mission.parking_departure)
    info=launch.metadata['injection']
    sol=dict(info,t_s=launch.arrays['t_s'],relative_state_si=np.c_[launch.arrays['r_m'],launch.arrays['v_m_s']])
    independent=verify_outgoing(spec,sol)
    dr=float(np.linalg.norm(planet[:3]+launch.arrays['r_m'][-1]-outer.arrays['r_m'][0]))
    dv=float(np.linalg.norm(planet[3:]+launch.arrays['v_m_s'][-1]-outer.arrays['v_m_s'][0]))
    dm=abs(float(launch.arrays['mass_kg'][-1]-outer.arrays['mass_kg'][0]))
    mass_error=float(np.max(np.abs(launch.arrays['mass_kg']-mission.mass_kg)))
    downstream_final=Trajectory.load(downstream/('final' if mission.capture else 'outer'))
    ep=Ephemerides().state(mission.departure,launch.metadata['epoch_jd']+launch.arrays['t_s']/DAY_S)
    expected_r=np.vstack([ep[:-1,:3]+launch.arrays['r_m'][:-1],downstream_final.arrays['r_m']])
    expected_v=np.vstack([ep[:-1,3:]+launch.arrays['v_m_s'][:-1],downstream_final.arrays['v_m_s']])
    cr=float(np.linalg.norm(joint.arrays['r_m']-expected_r,axis=1).max())
    cv=float(np.linalg.norm(joint.arrays['v_m_s']-expected_v,axis=1).max())
    expected_t=np.r_[launch.arrays['t_s'][:-1],launch.arrays['t_s'][-1]+downstream_final.arrays['t_s']]
    ct=float(np.max(np.abs(joint.arrays['t_s']-expected_t)))
    cm=float(np.max(np.abs(joint.arrays['mass_kg']-np.r_[launch.arrays['mass_kg'][:-1],downstream_final.arrays['mass_kg']])))
    cf=float(np.max(np.abs(joint.arrays['thrust_N']-np.r_[launch.arrays['thrust_N'][:-1],downstream_final.arrays['thrust_N']])))
    active_ok=np.array_equal(joint.arrays['active'],np.r_[launch.arrays['active'][:-1],downstream_final.arrays['active']])
    epoch_error=abs((launch.metadata['epoch_jd']+info['duration_s']/DAY_S-mission.launch_jd)*DAY_S)
    stamp=(launch.metadata['mission']==mission.to_dict() and launch.metadata['parking_departure']==asdict(spec)
           and joint.metadata['mission']==mission.to_dict() and launch.metadata['center']==mission.departure
           and joint.metadata['source_launch_arrays_sha256']==launch.metadata['arrays_sha256']
           and joint.metadata['source_downstream_arrays_sha256']==downstream_final.metadata['arrays_sha256']
           and launch.metadata['source_outer_arrays_sha256']==outer.metadata['arrays_sha256'])
    extra_ok=(launch.metadata['frame']=='ECLIPJ2000' and launch.metadata['time_scale']=='TDB'
              and joint.metadata['frame']=='ECLIPJ2000' and joint.metadata['time_scale']=='TDB'
              and joint.metadata['center']=='Sun' and joint.metadata['epoch_jd']==launch.metadata['epoch_jd']
              and np.all(launch.arrays['thrust_N']==0) and not launch.arrays['active'].any())
    if mission.departure_mode=='bounded_norm':extra_ok &= info['asymptotic_excess_m_s']<=mission.vinf_max_m_s+1e-5
    if mission.departure_mode=='fixed_norm':extra_ok &= abs(info['asymptotic_excess_m_s']-mission.vinf_max_m_s)<1e-5
    passed=(check['passed'] and independent['passed'] and dr<.1 and dv<1e-6 and dm<1e-6 and mass_error<1e-6
            and cr<.001 and cv<1e-8 and ct<1e-6 and cm<1e-6 and cf<1e-12 and active_ok and epoch_error<1e-4 and stamp and extra_ok)
    return dict(passed=bool(passed),kind='impulsive_parking_departure',join_position_error_m=dr,
                join_velocity_error_m_s=dv,join_mass_error_kg=dm,epoch_error_s=epoch_error,
                composition_position_error_m=cr,composition_velocity_error_m_s=cv,composition_time_error_s=ct,
                composition_mass_error_kg=cm,composition_thrust_error_N=cf,independent_launch=independent,downstream_verification=check,
                delta_v_m_s=info['delta_v_m_s'],interface_speed_m_s=info['interface_speed_m_s'],
                asymptotic_excess_m_s=info['asymptotic_excess_m_s'],departure_duration_days=info['duration_s']/DAY_S,
                injection_epoch_jd_tdb=launch.metadata['epoch_jd'],interface_epoch_jd_tdb=mission.launch_jd,
                payload_mass_kg=mission.mass_kg,upper_stage_propellant_kg=None,
                scope='Instantaneous tangential upper-stage impulse; payload-only mass. Patched Earth/Sun fields; free plane, no launch-site or finite-burn model.')


def run_launch_pipeline(mission,output,resume=False):
    from .capture_pipeline import run_capture_pipeline
    from .planetary_capture import correct_interface
    from .runner import run_pipeline
    from .runtime import runtime_environment
    output=Path(output);mission.validate()
    if resume:
        if Mission.load(output/'mission.json').to_dict()!=mission.to_dict():raise ValueError('Launch resume changes mission')
        saved=json.loads((output/'summary.json').read_text())
        if saved['status']=='completed':
            check=verify_launch_mission(output)
            if not check['passed']:raise ValueError('Saved parking departure failed acceptance')
            return Trajectory.load(output/'final'),saved
        if not (output/'coupling.json').exists():raise ValueError('No launch matching checkpoint to resume')
    output.mkdir(parents=True,exist_ok=resume)
    write_json(output/'mission.json',mission.to_dict());write_json(output/'environment.json',runtime_environment())
    summary=dict(case_id=mission.case_id,status='running',phase='parking_departure',launch_phase='seed',
                 completion_scope='parking_to_planetary_orbit' if mission.capture else 'parking_to_target',capture_included=bool(mission.capture))
    write_json(output/'summary.json',summary)
    spec=ParkingDeparture(**mission.parking_departure)
    planet=Ephemerides().state(mission.departure,mission.launch_jd)
    normal=np.cross(planet[:3],planet[3:]);normal/=np.linalg.norm(normal)
    seed_path=mission.solver.get('launch_seed_path')
    if seed_path:
        path=Path(seed_path);seed=Trajectory.load(path/('outer' if (path/'outer').exists() else 'final'))
    else:
        base=replace(mission,parking_departure=None,departure_offset_state_si=None)
        _,status=run_pipeline(base,output/'seed_chain')
        if status['status']!='completed':raise RuntimeError('A physical interplanetary seed is required for launch coupling')
        seed=Trajectory.load(output/'seed_chain'/('outer' if mission.capture else 'final'))
    history=json.loads((output/'coupling.json').read_text())['history'] if resume else []
    started=perf_counter();latest=seed
    if resume:
        warm=output/f'warm_{len(history):02d}'
        if warm.exists():latest=Trajectory.load(warm)
        elif history:latest=Trajectory.load(output/history[-1]['downstream_folder']/('outer'))
    try:
        for index in range(len(history),int(mission.solver.get('launch_max_iterations',10))):
            if perf_counter()-started>float(mission.solver.get('launch_budget_s',900)):raise TimeoutError('Launch matching budget reached')
            speed=latest.arrays['v_m_s'][0]-planet[3:]
            launch=outgoing_hyperbola(spec,speed,normal)
            offset=np.r_[launch['relative_state_si'][-1,:3],0.,0.,0.].tolist()
            settings=dict(mission.solver,capture_seed_path=str((output/f'warm_{index:02d}').as_posix()))
            if not (output/f'warm_{index:02d}').exists():latest.save(output/f'warm_{index:02d}')
            resolved=replace(mission,departure_offset_state_si=offset,solver=settings)
            folder=output/f'match_{index:02d}'
            summary.update(launch_phase='downstream_matching',downstream_folder=folder.name)
            write_json(output/'summary.json',summary)
            if mission.capture:
                _,result=run_capture_pipeline(resolved,folder,resume=folder.exists())
                if result['status']!='completed':raise RuntimeError('Downstream capture stopped: '+result.get('capture_phase','')+'; '+result.get('error',''))
                latest=Trajectory.load(folder/'outer')
                downstream=Trajectory.load(folder/'final')
            else:
                folder.mkdir();latest,request=correct_interface(latest,resolved)
                latest.save(folder/'outer');write_json(folder/'request.json',request);write_json(folder/'mission.json',resolved.to_dict())
                latest=Trajectory.load(folder/'outer');downstream=latest
            # Rebuild using the actual, corrected velocity, not a frozen seed.
            launch=outgoing_hyperbola(spec,latest.arrays['v_m_s'][0]-planet[3:],normal)
            error=float(np.linalg.norm(planet[:3]+launch['relative_state_si'][-1,:3]-latest.arrays['r_m'][0]))
            history.append(dict(iteration=index,position_match_error_m=error,delta_v_m_s=launch['delta_v_m_s'],downstream_folder=folder.name))
            write_json(output/'coupling.json',dict(history=history))
            print('launch interface matching',index,error,flush=True)
            if error<.05:break
        else:raise RuntimeError('Launch interface did not converge within the common iteration limit')
        info={k:v for k,v in launch.items() if k not in ('t_s','relative_state_si')}
        epoch=mission.launch_jd-launch['duration_s']/DAY_S
        meta=dict(case_id=mission.case_id,epoch_jd=epoch,time_scale='TDB',frame='ECLIPJ2000',center=mission.departure,
                  model='Earth two-body hyperbola after instantaneous tangential upper-stage impulse',status='pending_verification',
                  stage='parking_departure',title='Отлёт с НОО: разгонный блок',mission=mission.to_dict(),parking_departure=asdict(spec),injection=info,
                  source_outer_arrays_sha256=latest.metadata['arrays_sha256'],mass_scope='Payload after upper-stage separation; no upper-stage propellant model')
        a=dict(t_s=launch['t_s'],r_m=launch['relative_state_si'][:,:3],v_m_s=launch['relative_state_si'][:,3:],
               mass_kg=np.full(len(launch['t_s']),mission.mass_kg),thrust_N=np.zeros(len(launch['t_s'])),active=np.zeros(len(launch['t_s']),dtype=bool))
        segment=Trajectory(meta,a);segment.save(output/'launch');segment=Trajectory.load(output/'launch')
        ep=Ephemerides().state(mission.departure,epoch+launch['t_s']/DAY_S)
        arrays=dict(t_s=np.r_[a['t_s'][:-1],a['t_s'][-1]+downstream.arrays['t_s']],
                    r_m=np.vstack([ep[:-1,:3]+a['r_m'][:-1],downstream.arrays['r_m']]),
                    v_m_s=np.vstack([ep[:-1,3:]+a['v_m_s'][:-1],downstream.arrays['v_m_s']]),
                    mass_kg=np.r_[a['mass_kg'][:-1],downstream.arrays['mass_kg']],
                    thrust_N=np.r_[a['thrust_N'][:-1],downstream.arrays['thrust_N']],
                    active=np.r_[a['active'][:-1],downstream.arrays['active']])
        joint_meta=dict(meta,center='Sun',model='Patched Earth departure, Sun transfer and optional planetary capture',stage='launch_mission',
                        title='НОО → '+mission.target+': отлёт, перелёт и прибытие',
                        source_launch_arrays_sha256=segment.metadata['arrays_sha256'],source_downstream_arrays_sha256=downstream.metadata['arrays_sha256'],
                        join_time_s=launch['duration_s'],capture_included=bool(mission.capture))
        joint_meta['overlays']=downstream.metadata.get('overlays',[])
        for overlay in joint_meta['overlays']:arrays[overlay['array']]=downstream.arrays[overlay['array']]
        joint_meta['markers']=downstream.metadata.get('markers',[])
        if mission.capture:joint_meta['capture_join_time_s']=launch['duration_s']+mission.tof_days*DAY_S
        joint=Trajectory(joint_meta,arrays);joint.save(output/'final')
        summary['launch_phase']='verification';write_json(output/'summary.json',summary)
        check=verify_launch_mission(output)
        if not check['passed']:raise RuntimeError('Launch stitch failed independent acceptance: '+str(check))
        write_json(output/'verification.json',check)
        segment.metadata.update(status='verified_launch')
        write_json(output/'launch/trajectory.json',segment.metadata)
        joint=Trajectory.load(output/'final');joint.metadata.update(status='verified_launch',verification=check)
        write_json(output/'final/trajectory.json',joint.metadata)
        summary.update(status='completed',phase='final',verification=check,arrays_sha256=Trajectory.load(output/'final').metadata['arrays_sha256'])
        write_json(output/'summary.json',summary)
        from .visualization import render
        render(segment,output/'launch_plots');render(joint,output/'plots')
        return Trajectory.load(output/'final'),summary
    except (ValueError,RuntimeError,TimeoutError) as exc:
        summary.update(status='partial',error=str(exc),stop_kind='launch_'+summary['launch_phase']+'_failed')
        write_json(output/'summary.json',summary)
        return latest,summary
