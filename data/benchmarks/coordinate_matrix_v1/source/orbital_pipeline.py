"""One controller for the four local departure/arrival combinations."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import json
import numpy as np
from scipy.optimize import brentq
from .data import Trajectory,Scales,DAY_S,write_json,sha256
from .problem import Mission
from .ephemerides import Ephemerides
from .contract import make_request,audit_configuration,configuration_hash,specification,digest
from .orbital_maneuvers import (spiral_departure,orient_departure,incoming_impulse,
                               capture_impulse_event,replay_transverse)
from .parking_departure import ParkingDeparture,outgoing_hyperbola,verify_outgoing
from .planetary_capture import CaptureOrbit,backward_capture,orient_capture,forward_capture,elements


def correct_outer(seed,mission,folder):
    """Continue both boundaries and actual spacecraft mass to the request.

    Every accepted continuation point is a physical PSI for its stated input;
    it is not advertised as a locally stitched orbit until the final join.
    """
    from .bounded_model import BoundedModel
    from .bangbang import solve_bangbang
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    old=Mission(**seed.metadata['mission'])
    if (old.launch_tdb,old.tof_days,old.departure,old.target)!=(mission.launch_tdb,mission.tof_days,mission.departure,mission.target):raise ValueError('Outer warm seed uses different dates or bodies')
    if not (seed.metadata['bounded_model']['alpha']==1 and seed.metadata['bounded_model']['beta']==1):raise ValueError('Orbital matching requires a physical PSI seed')
    eph=mission.ephemerides();earth=eph.state(mission.departure,mission.launch_jd)
    target_body=eph.state(mission.target,mission.arrival_jd)
    start_old=np.asarray(seed.metadata['body_initial_state_si'])-earth
    # The nominal body's velocity is not an orbital velocity offset. Its tiny
    # round-trip normalization error belongs to the seed, not the request.
    start_old[3:]=0.
    target_old=np.asarray(seed.metadata['target_state_si'])-target_body
    start_new=np.asarray(mission.departure_offset_state_si);target_new=np.asarray(mission.arrival_offset_state_si)
    v_old=seed.arrays['v_m_s'][0]-earth[3:]
    new_departure_face=mission.departure_mode=='fixed_vector' and old.departure_mode!='fixed_vector'
    if new_departure_face:
        # A change of initial-velocity transversality can change the number of
        # thrust arcs. Rebuild through the existing ILTT/Pazov/PSI chain rather
        # than assume the old free-departure switching topology survives.
        from .runner import _run_pipeline
        result,status=_run_pipeline(mission,folder/'seed_chain')
        if status['status']!='completed':
            write_json(folder/'continuation.json',dict(reached=0.,history=[],seed_summary=status))
            raise RuntimeError('Physical outer seed stopped at '+status.get('phase','unknown')+': '+status.get('error','partial continuation'))
        result.save(folder/'accepted_seed')
        write_json(folder/'continuation.json',dict(reached=1.,history=[dict(parameter=1.,accepted=True,artifact='accepted_seed')]))
        return Trajectory.load(folder/'accepted_seed'),make_request(mission)
    at=0.;step=1.;current=seed;history=[];failures=0
    while at<1:
        value=min(1.,at+step)
        hw={k:old.spacecraft[k]+value*(mission.spacecraft[k]-old.spacecraft[k]) for k in mission.spacecraft}
        mass=old.mass_kg+value*(mission.mass_kg-old.mass_kg)
        interim=replace(mission,mass_kg=mass,spacecraft=hw,
                        departure_offset_state_si=(start_old+value*(start_new-start_old)).tolist(),
                        arrival_offset_state_si=(target_old+value*(target_new-target_old)).tolist())
        if mission.departure_mode=='fixed_vector':interim=replace(interim,vinf_vector_m_s=(v_old+value*(np.asarray(mission.vinf_vector_m_s)-v_old)).tolist())
        if value==1.:interim=mission;hw=mission.spacecraft;mass=mission.mass_kg
        body,target,scale=interim.boundary()
        context=deepcopy(current);previous=deepcopy(current)
        ratio=mass/current.metadata['mission']['mass_kg']
        previous.arrays['mass_kg']*=ratio;previous.metadata['mission']['mass_kg']=mass
        context.metadata.update(mission=interim.to_dict(),case_id=mission.case_id,body_initial_state_si=body.tolist(),
                                target_state_si=target.tolist(),configuration_sha256=configuration_hash(interim),status='unverified_boundary_seed')
        context.metadata.pop('verification',None)
        model=BoundedModel(a_max=hw['thrust_N']/mass/scale.acceleration_m_s2,alpha=1.,beta=1.,
                           q=hw['thrust_N']*scale.time_s/(mass*hw['exhaust_velocity_m_s']),variable_mass=True)
        try:
            attempt=float(mission.solver.get('orbital_attempt_s',60))
            result=solve_bangbang(context,previous,model,perf_counter()+attempt,'psi')
            request=make_request(interim);audit_configuration(result,interim,request,require_final=True)
        except (ValueError,RuntimeError,TimeoutError) as exc:
            history.append(dict(parameter=value,accepted=False,error=str(exc)));write_json(folder/'continuation.json',dict(history=history,reached=at))
            failures+=1;step*=.5
            if failures>=3 or step<1/64:raise RuntimeError('Outer boundary continuation stopped: '+str(exc)) from exc
            continue
        at=value;current=result;failures=0;step=min(1.,step*1.5)
        destination=folder/f'accepted_{len(history):03d}';current.save(destination)
        current=Trajectory.load(destination);write_json(destination/'request.json',request)
        history.append(dict(parameter=value,accepted=True,artifact=destination.name))
        write_json(folder/'continuation.json',dict(history=history,reached=at))
    return current,make_request(mission)


def _segment(mission,side,solution,epoch,center,info):
    y=solution['relative_state_si'];t=solution['t_s']
    meta=dict(case_id=mission.case_id,epoch_jd=epoch,time_scale='TDB',frame='ECLIPJ2000',center=center,
              model='patched central-field orbital '+side,status='pending_verification',stage='orbital_'+side,
              mission=mission.to_dict(),maneuver=info)
    arrays=dict(t_s=t,r_m=y[:,:3],v_m_s=y[:,3:],mass_kg=solution['mass_kg'],thrust_N=solution['thrust_N'],active=solution['thrust_N']>0)
    return Trajectory(meta,arrays)


def run_orbital_pipeline(mission,output,resume=False):
    from .runtime import runtime_environment
    output=Path(output);mission.validate()
    if mission.orbital_maneuvers['arrival'].get('duration_search') is not None:
        from .capture_search import run_capture_search
        return run_capture_search(mission,output,resume=resume)
    recovered_seed=None
    if mission.mass_reference!='initial_orbit':raise ValueError('Solve expects mass_kg at the initial orbit, not an internal resolved mission')
    if resume:
        if Mission.load(output/'mission.json').to_dict()!=mission.to_dict():raise ValueError('Orbital resume changes requested parameters')
        s=json.loads((output/'summary.json').read_text())
        if s['status']=='completed':
            check=verify_orbital_mission(output)
            if not check['passed']:raise ValueError('Saved orbital mission failed replay')
            return Trajectory.load(output/'final'),s
        checkpoints=sorted(output.glob('match_*/continuation.json'))
        for checkpoint in reversed(checkpoints):
            accepted=[x for x in json.loads(checkpoint.read_text())['history'] if x['accepted']]
            if accepted:
                recovered_seed=Trajectory.load(checkpoint.parent/accepted[-1]['artifact']);break
        if recovered_seed is None:raise ValueError('No accepted physical outer checkpoint to resume')
        counter=0
        while (output/f'resume_{counter:03d}_summary.json').exists():counter+=1
        write_json(output/f'resume_{counter:03d}_summary.json',s)
    output.mkdir(parents=True,exist_ok=resume)
    write_json(output/'mission.json',mission.to_dict());write_json(output/'environment.json',runtime_environment())
    root_request=dict(mission=specification(mission),configuration_sha256=configuration_hash(mission))
    write_json(output/'request.json',dict(root_request,request_sha256=digest(root_request)))
    modes=mission.orbital_maneuvers;d,a=modes['departure'],modes['arrival']
    summary=dict(case_id=mission.case_id,status='running',phase='orbital_maneuvers',orbital_phase='departure',
                 departure_kind=d['kind'],arrival_kind=a['kind'],completion_scope='initial_orbit_to_final_orbit')
    write_json(output/'summary.json',summary)
    F=mission.spacecraft['thrust_N'];c=mission.spacecraft['exhaust_velocity_m_s']
    dry=mission.spacecraft['dry_mass_kg'];eph=mission.ephemerides()
    earth=eph.state(mission.departure,mission.launch_jd);planet=eph.state(mission.target,mission.arrival_jd)
    normal=np.cross(earth[:3],earth[3:]);normal/=np.linalg.norm(normal)
    parking=ParkingDeparture(**{k:v for k,v in d.items() if k!='kind'})
    orbit=CaptureOrbit(**{k:a[k] for k in CaptureOrbit.__dataclass_fields__})
    cache={};history=json.loads((output/'coupling.json').read_text())['history'] if resume and (output/'coupling.json').exists() else []
    current=None;index_offset=len(list(output.glob('match_*/continuation.json')))
    try:
        seed_hint=mission.solver.get('orbital_seed_path')
        if recovered_seed is not None:current=recovered_seed
        elif seed_hint:
            seed_path=Path(seed_hint)
            current=Trajectory.load(seed_path if (seed_path/'trajectory.json').exists() else seed_path/('outer' if (seed_path/'outer').exists() else 'final'))
        else:
            from .runner import run_pipeline
            summary['orbital_phase']='interplanetary_seed';write_json(output/'summary.json',summary)
            base=replace(mission,orbital_maneuvers=None,mass_reference=None,departure_offset_state_si=None,arrival_offset_state_si=None)
            current,seed_status=run_pipeline(base,output/'seed_chain')
            if seed_status['status']!='completed':raise RuntimeError('Interplanetary seed unavailable: '+seed_status.get('error','partial seed chain'))
            summary['orbital_phase']='departure';write_json(output/'summary.json',summary)
        velocity=current.arrays['v_m_s'][0]-earth[3:]
        if d['kind']=='spiral':
            base=spiral_departure(parking,mission.mass_kg,F,c)
            departure=orient_departure(base,velocity,normal)
            transfer_mass=departure['interface_mass_kg']
        else:transfer_mass=mission.mass_kg
        if transfer_mass<dry:raise ValueError('dry_mass_constraint: departure alone exhausts the usable spacecraft propellant')
        desired_mass=float(current.arrays['mass_kg'][-1])
        started=perf_counter()
        for index in range(index_offset,index_offset+int(mission.solver.get('orbital_max_iterations',16))):
            if perf_counter()-started>float(mission.solver.get('orbital_budget_s',1200)):raise TimeoutError('Common orbital matching budget reached')
            if d['kind']=='impulse':
                departure=outgoing_hyperbola(parking,current.arrays['v_m_s'][0]-earth[3:],normal)
                departure.update(mass_kg=np.full(len(departure['t_s']),mission.mass_kg),thrust_N=np.zeros(len(departure['t_s'])))
            if a['kind']=='spiral':
                summary['orbital_phase']='arrival_construction';write_json(output/'summary.json',summary)
                def nominal(mf):
                    key=float(mf)
                    if key not in cache:cache[key]=orient_capture(backward_capture(orbit,key,F,c,control=a.get('capture_control'),max_days=a.get('max_capture_days',2000.)),planet)
                    return cache[key]
                if desired_mass<=dry:raise ValueError('dry_mass_constraint: no propellant remains for the arrival spiral')
                low=nominal(dry)['entry_mass_kg']-desired_mass
                if low>0:raise ValueError('dry_mass_constraint: the arrival spiral would finish below the requested dry mass')
                mf=brentq(lambda m:nominal(m)['entry_mass_kg']-desired_mass,dry,desired_mass,xtol=1e-8)
                arrival=nominal(mf)
            else:arrival=orient_capture(incoming_impulse(a,desired_mass),planet)
            offset=np.r_[departure['relative_state_si'][-1,:3],0.,0.,0.].tolist()
            resolved=replace(mission,mass_kg=transfer_mass,mass_reference='interplanetary_departure',
                             departure_offset_state_si=offset,arrival_offset_state_si=arrival['relative_state_si'][0].tolist())
            if d['kind']=='spiral':resolved=replace(resolved,departure_mode='fixed_vector',vinf_vector_m_s=departure['relative_state_si'][-1,3:].tolist())
            summary['orbital_phase']='interplanetary_matching';write_json(output/'summary.json',summary)
            current,request=correct_outer(current,resolved,output/f'match_{index:02d}')
            checkpoint=json.loads((output/f'match_{index:02d}'/'continuation.json').read_text())
            accepted=[x for x in checkpoint['history'] if x['accepted']]
            summary['last_verified_artifact']=str(output/f'match_{index:02d}'/accepted[-1]['artifact'])
            incoming_mass=float(current.arrays['mass_kg'][-1])
            if d['kind']=='impulse':
                departure=outgoing_hyperbola(parking,current.arrays['v_m_s'][0]-earth[3:],normal)
                departure.update(mass_kg=np.full(len(departure['t_s']),mission.mass_kg),thrust_N=np.zeros(len(departure['t_s'])))
            dr=float(np.linalg.norm(earth[:3]+departure['relative_state_si'][-1,:3]-current.arrays['r_m'][0]))
            dm=abs(incoming_mass-desired_mass) if a['kind']=='spiral' else 0.
            history.append(dict(iteration=index,departure_position_error_m=dr,arrival_mass_error_kg=dm,
                                outer_final_mass_kg=incoming_mass,outer_arrays_sha256=current.metadata['arrays_sha256']))
            write_json(output/'coupling.json',dict(history=history))
            print('orbital matching',index,dr,dm,flush=True)
            desired_mass=incoming_mass
            if dr<.05 and dm<1e-7:break
        else:raise RuntimeError('Common orbital interface iteration limit reached')
        summary['orbital_phase']='local_propagation';write_json(output/'summary.json',summary)
        for name in ('outer','departure','arrival','final'):
            if (output/name).exists():
                counter=0
                while (output/f'{name}_previous_{counter:03d}').exists():counter+=1
                (output/name).rename(output/f'{name}_previous_{counter:03d}')
        current.save(output/'outer');write_json(output/'outer_request.json',request);current=Trajectory.load(output/'outer')
        state=np.r_[current.arrays['r_m'][-1],current.arrays['v_m_s'][-1]]-planet
        events=[]
        if a['kind']=='spiral':
            physical=forward_capture(orbit,state,desired_mass,F,c,arrival['burn_start_s'],arrival['duration_s'],sample_times=arrival['t_s'],
                                     control=arrival.get('control'),reference_axis=arrival.get('reference_axis'))
            arrival_info=dict(kind='spiral',burn_start_s=arrival['burn_start_s'],duration_s=arrival['duration_s'])
            if 'control' in arrival:
                arrival_info.update(control=arrival['control'],reference_axis=arrival['reference_axis'],arcs=physical['arcs'],
                                    active_duration_s=physical['active_duration_s'])
            final_state=physical['relative_state_si'][-1];final_mass=float(physical['mass_kg'][-1])
        else:
            t=arrival['t_s'];replay=replay_transverse(state,desired_mass,orbit.mu_m3_s2,0.,c,arrival['duration_s'],t)
            physical=dict(t_s=t,relative_state_si=replay[:,:6],mass_kg=replay[:,6],thrust_N=np.zeros(len(t)))
            event=capture_impulse_event(replay[-1,:6],desired_mass,a,departure['duration_s']+mission.tof_days*DAY_S+arrival['duration_s'])
            events.append(event);arrival_info=dict(kind='impulse',duration_s=arrival['duration_s'])
            final_state=np.asarray(event['state_after_si']);final_mass=event['mass_after_kg']
        if final_mass<dry-1e-6:raise ValueError('dry_mass_constraint: arrival finishes below the requested dry mass')
        dep_info=dict(kind=d['kind'],duration_s=departure['duration_s'])
        if d['kind']=='impulse':
            info={k:v for k,v in departure.items() if k not in ('t_s','relative_state_si','mass_kg','thrust_N')}
            dep_info['injection']=info
            events.insert(0,dict(kind='external_upper_stage',time_s=0.,delta_v_vector_m_s=info['delta_v_vector_m_s'],
                                delta_v_m_s=info['delta_v_m_s'],payload_mass_before_kg=mission.mass_kg,payload_mass_after_kg=mission.mass_kg,
                                upper_stage_propellant_kg=None,mass_scope='spacecraft only; external upper stage excluded'))
        epoch=mission.launch_jd-departure['duration_s']/DAY_S
        dep=_segment(mission,'departure',departure,epoch,mission.departure,dep_info)
        arr=_segment(mission,'arrival',physical,mission.arrival_jd,mission.target,arrival_info)
        dep.save(output/'departure');arr.save(output/'arrival')
        dep=Trajectory.load(output/'departure');arr=Trajectory.load(output/'arrival')
        write_json(output/'impulses.json',events)
        es=eph.state(mission.departure,epoch+dep.arrays['t_s'][:-1]/DAY_S)
        ps=eph.state(mission.target,mission.arrival_jd+arr.arrays['t_s'][1:]/DAY_S)
        arrays=dict(t_s=np.r_[dep.arrays['t_s'][:-1],departure['duration_s']+current.arrays['t_s'],departure['duration_s']+mission.tof_days*DAY_S+arr.arrays['t_s'][1:]],
                    r_m=np.vstack([es[:,:3]+dep.arrays['r_m'][:-1],current.arrays['r_m'],ps[:,:3]+arr.arrays['r_m'][1:]]),
                    v_m_s=np.vstack([es[:,3:]+dep.arrays['v_m_s'][:-1],current.arrays['v_m_s'],ps[:,3:]+arr.arrays['v_m_s'][1:]]),
                    mass_kg=np.r_[dep.arrays['mass_kg'][:-1],current.arrays['mass_kg'],arr.arrays['mass_kg'][1:]],
                    thrust_N=np.r_[dep.arrays['thrust_N'][:-1],current.arrays['thrust_N'],arr.arrays['thrust_N'][1:]],
                    active=np.r_[dep.arrays['active'][:-1],current.arrays['active'],arr.arrays['active'][1:]])
        if a['kind']=='impulse':
            end_planet=eph.state(mission.target,mission.arrival_jd+arrival['duration_s']/DAY_S)
            arrays['r_m'][-1]=end_planet[:3]+final_state[:3];arrays['v_m_s'][-1]=end_planet[3:]+final_state[3:]
            arrays['mass_kg'][-1]=final_mass
        meta=dict(case_id=mission.case_id,epoch_jd=epoch,time_scale='TDB',frame='ECLIPJ2000',center='Sun',
                  stage='orbital_mission',model='patched central fields with explicit orbital maneuvers',status='pending_verification',
                  mission=mission.to_dict(),source_arrays_sha256={k:Trajectory.load(output/k).metadata['arrays_sha256'] for k in ('departure','outer','arrival')},
                  impulses_sha256=sha256(output/'impulses.json'))
        Trajectory(meta,arrays).save(output/'final')
        summary['orbital_phase']='verification';write_json(output/'summary.json',summary)
        check=verify_orbital_mission(output)
        write_json(output/'verification.json',check)
        if not check.get('capture_budget',{}).get('passed',True):raise RuntimeError('capture_budget_constraint: '+str(check['capture_budget']['checks']))
        if not check['passed']:raise RuntimeError('Orbital mission acceptance failed: '+str(check))
        final=Trajectory.load(output/'final');final.metadata.update(status='verified_orbital_mission',verification=check)
        write_json(output/'final/trajectory.json',final.metadata)
        summary.update(status='completed',phase='final',verification=check,arrays_sha256=final.metadata['arrays_sha256'])
        write_json(output/'summary.json',summary)
        from .orbital_visualization import render_orbital_mission
        render_orbital_mission(output,output/'plots')
        return final,summary
    except (ValueError,RuntimeError,TimeoutError) as exc:
        message=str(exc)
        summary.update(status='partial',error=message,stop_kind='dry_mass_constraint' if ('dry_mass_constraint' in message or 'dry mass constraint' in message) else 'orbital_'+summary['orbital_phase']+'_failed')
        if 'capture_budget_constraint' in message:summary['stop_kind']='capture_budget_constraint'
        if 'capture_duration_limit' in message:summary['stop_kind']='capture_duration_limit'
        if 'capture_control:' in message:summary['stop_kind']='capture_control_domain'
        seed_summaries=sorted(output.glob('match_*/seed_chain/summary.json'))
        if seed_summaries:
            nested=json.loads(seed_summaries[-1].read_text())
            summary['outer_seed_summary']=str(seed_summaries[-1])
            summary['outer_seed_phase']=nested.get('phase')
        write_json(output/'summary.json',summary)
        return current,summary


def verify_orbital_mission(folder):
    """Verify physical local laws, events, request and the entire composition."""
    from .bounded import verify_bounded
    from .kiam_verification import verify_kiam_psi
    from .data import sha256
    from .orbital_maneuvers import replay_departure_spiral
    p=Path(folder);m=Mission.load(p/'mission.json');d=m.orbital_maneuvers['departure'];a=m.orbital_maneuvers['arrival']
    if a.get('duration_search') is not None:
        from .capture_search import verify_capture_search
        return verify_capture_search(p)
    if m.mass_reference!='initial_orbit':raise ValueError('Orbital root mass must refer to the initial orbit')
    root=json.loads((p/'request.json').read_text());payload={k:v for k,v in root.items() if k!='request_sha256'}
    if digest(payload)!=root['request_sha256'] or root['mission']!=specification(m) or root['configuration_sha256']!=configuration_hash(m):raise ValueError('Orbital root request mismatch')
    dep,outer,arr,joint=[Trajectory.load(p/name) for name in ('departure','outer','arrival','final')]
    modes=[(dep,m.departure,'departure'),(arr,m.target,'arrival')]
    for segment,center,side in modes:
        if segment.metadata['mission']!=m.to_dict() or segment.metadata['center']!=center or segment.metadata['frame']!='ECLIPJ2000' or segment.metadata['time_scale']!='TDB':raise ValueError('Orbital segment metadata mismatch: '+side)
        if segment.metadata['maneuver']['kind']!=m.orbital_maneuvers[side]['kind']:raise ValueError('Orbital maneuver mode differs from request')
    if joint.metadata['mission']!=m.to_dict() or joint.metadata['center']!='Sun' or joint.metadata['frame']!='ECLIPJ2000' or joint.metadata['time_scale']!='TDB':raise ValueError('Joint mission metadata mismatch')
    links=all(joint.metadata['source_arrays_sha256'][k]==Trajectory.load(p/k).metadata['arrays_sha256'] for k in ('departure','outer','arrival'))
    links &= joint.metadata['impulses_sha256']==sha256(p/'impulses.json')
    ep=m.ephemerides();earth=ep.state(m.departure,m.launch_jd);planet=ep.state(m.target,m.arrival_jd)
    D=dep.arrays;O=outer.arrays;A=arr.arrays;J=joint.arrays
    desired=replace(m,mass_kg=float(D['mass_kg'][-1]),mass_reference='interplanetary_departure',
                    departure_offset_state_si=outer.metadata['mission']['departure_offset_state_si'],
                    arrival_offset_state_si=outer.metadata['mission']['arrival_offset_state_si'])
    if d['kind']=='spiral':desired=replace(desired,departure_mode='fixed_vector',vinf_vector_m_s=outer.metadata['mission']['vinf_vector_m_s'])
    audit=audit_configuration(outer,desired,json.loads((p/'outer_request.json').read_text()),require_final=True)
    left_r=float(np.linalg.norm(earth[:3]+D['r_m'][-1]-O['r_m'][0]))
    left_v=float(np.linalg.norm(earth[3:]+D['v_m_s'][-1]-O['v_m_s'][0]))
    left_m=abs(float(D['mass_kg'][-1]-O['mass_kg'][0]))
    right_r=float(np.linalg.norm(planet[:3]+A['r_m'][0]-O['r_m'][-1]))
    right_v=float(np.linalg.norm(planet[3:]+A['v_m_s'][0]-O['v_m_s'][-1]))
    right_m=abs(float(A['mass_kg'][0]-O['mass_kg'][-1]))
    time_error=max(abs((dep.metadata['epoch_jd']+D['t_s'][-1]/DAY_S-m.launch_jd)*DAY_S),
                   abs((arr.metadata['epoch_jd']-m.arrival_jd)*DAY_S),abs(joint.metadata['epoch_jd']-dep.metadata['epoch_jd'])*DAY_S)
    F=m.spacecraft['thrust_N'];c=m.spacecraft['exhaust_velocity_m_s'];dry=m.spacecraft['dry_mass_kg']
    parking=ParkingDeparture(**{k:v for k,v in d.items() if k!='kind'})
    dep_state=np.c_[D['r_m'],D['v_m_s']];arr_state=np.c_[A['r_m'],A['v_m_s']]
    rp=parking.planet_radius_m+parking.parking_altitude_m
    circular=(abs(np.linalg.norm(dep_state[0,:3])-rp)<.01 and abs(dep_state[0,:3]@dep_state[0,3:])<1.
              and abs(D['mass_kg'][0]-m.mass_kg)<1e-7)
    interface_radii=(abs(float(np.linalg.norm(dep_state[-1,:3]))-parking.interface_radius_m)<.1
                     and abs(float(np.linalg.norm(arr_state[0,:3]))-a['interface_radius_m'])<m.position_tolerance_m)
    departure_mass_flow=abs(float(m.mass_kg-D['mass_kg'][-1])-(F/c*D['t_s'][-1] if d['kind']=='spiral' else 0.))
    if d['kind']=='spiral':
        replay=replay_departure_spiral(parking,dep_state[0],m.mass_kg,F,c,D['t_s'])
        dep_r=float(np.linalg.norm(replay[:,:3]-D['r_m'],axis=1).max());dep_v=float(np.linalg.norm(replay[:,3:6]-D['v_m_s'],axis=1).max())
        dep_m=float(np.abs(replay[:,6]-D['mass_kg']).max())
        dep_ok=(dep_r<100. and dep_v<.001 and dep_m<1e-6 and np.all(D['thrust_N']==F)
                and np.all(D['active']) and abs(np.linalg.norm(dep_state[0,3:])-np.sqrt(parking.mu_m3_s2/rp))<1e-7)
        dep_check=dict(passed=bool(dep_ok),position_error_m=dep_r,velocity_error_m_s=dep_v,mass_error_kg=dep_m,
                       method='Independent angular-rate polar equations, LSODA; primary angular momentum equations, DOP853')
    else:
        sol=dict(dep.metadata['maneuver']['injection'],t_s=D['t_s'],relative_state_si=dep_state)
        dep_check=verify_outgoing(parking,sol);dep_ok=dep_check['passed'] and np.all(D['thrust_N']==0) and not D['active'].any()
    orbit=CaptureOrbit(**{k:a[k] for k in CaptureOrbit.__dataclass_fields__})
    info=arr.metadata['maneuver']
    phase_times=(dep.metadata['maneuver']['duration_s']==D['t_s'][-1] and info['duration_s']==A['t_s'][-1])
    if a['kind']=='spiral':
        replay=forward_capture(orbit,arr_state[0],float(A['mass_kg'][0]),F,c,info['burn_start_s'],info['duration_s'],sample_times=A['t_s'],
                               control=a.get('capture_control'),reference_axis=info.get('reference_axis'))
        indices=np.searchsorted(replay['t_s'],A['t_s']);replayed=replay['relative_state_si'][indices];replayed_mass=replay['mass_kg'][indices]
        expected_fuel=F/c*(info['duration_s']-info['burn_start_s'])
        thrust_ok=np.array_equal(A['thrust_N'],np.where(A['t_s']>=info['burn_start_s'],F,0.))
        if a.get('capture_control') is not None:
            from dataclasses import asdict
            from .capture_control import CaptureControl
            from .angular_capture import schedule_throttle
            if info.get('control')!=asdict(CaptureControl(**a['capture_control'])):raise ValueError('Capture control differs from request')
            arcs=info['arcs'];independent=replay['arcs']
            schedule_ok=(len(arcs)==len(independent) and all(x['active']==y['active'] and
                         abs(x['start_s']-y['start_s'])<.05 and abs(x['end_s']-y['end_s'])<.05 for x,y in zip(arcs,independent)))
            schedule_ok &= bool(arcs) and arcs[0]['start_s']==0 and abs(arcs[-1]['end_s']-info['duration_s'])<1e-6
            schedule_ok &= all(x['end_s']>x['start_s'] and isinstance(x['active'],bool) for x in arcs)
            schedule_ok &= all(abs(x['end_s']-y['start_s'])<1e-6 for x,y in zip(arcs[:-1],arcs[1:]))
            active_time=sum(x['end_s']-x['start_s'] for x in arcs if x['active'])
            schedule_ok &= abs(active_time-info['active_duration_s'])<1e-6
            axis=np.asarray(info['reference_axis']);schedule_ok &= abs(np.linalg.norm(axis)-1)<1e-10
            schedule_ok &= np.linalg.norm(axis-arr_state[-1,:3]/np.linalg.norm(arr_state[-1,:3]))<1e-4
            expected_fuel=F/c*active_time
            thrust_ok=schedule_ok and np.array_equal(A['thrust_N'],F*schedule_throttle(A['t_s'],arcs))
            thrust_ok &= np.array_equal(A['active'],A['thrust_N']>0)
    else:
        replayed_all=replay_transverse(arr_state[0],float(A['mass_kg'][0]),orbit.mu_m3_s2,0.,c,info['duration_s'],A['t_s'])
        replayed=replayed_all[:,:6];replayed_mass=replayed_all[:,6];expected_fuel=0.;thrust_ok=np.all(A['thrust_N']==0)
        excess2=float(arr_state[0,3:]@arr_state[0,3:]-2*orbit.mu_m3_s2/np.linalg.norm(arr_state[0,:3]))
        thrust_ok &= excess2>0 and abs(np.sqrt(excess2)-a['excess_velocity_m_s'])<m.velocity_tolerance_m_s
        thrust_ok &= float(arr_state[0,:3]@arr_state[0,3:])<0
    arr_r=float(np.linalg.norm(replayed[:,:3]-A['r_m'],axis=1).max());arr_v=float(np.linalg.norm(replayed[:,3:]-A['v_m_s'],axis=1).max())
    arr_m=float(np.max(abs(replayed_mass-A['mass_kg'])))
    arrival_flow=abs(float(A['mass_kg'][0]-A['mass_kg'][-1])-expected_fuel)
    events=json.loads((p/'impulses.json').read_text());expected_events=int(d['kind']=='impulse')+int(a['kind']=='impulse')
    event_ok=len(events)==expected_events;event_residuals=[]
    end_local=arr_state[-1].copy();end_mass=float(A['mass_kg'][-1])
    if d['kind']=='impulse':
        e=events[0];inj=dep.metadata['maneuver']['injection']
        event_ok &= (e['kind']=='external_upper_stage' and e['time_s']==0 and e['payload_mass_before_kg']==m.mass_kg
                     and e['payload_mass_after_kg']==m.mass_kg and e['upper_stage_propellant_kg'] is None
                     and np.linalg.norm(np.asarray(e['delta_v_vector_m_s'])-inj['delta_v_vector_m_s'])<1e-8
                     and abs(e['delta_v_m_s']-inj['delta_v_m_s'])<1e-8)
    if a['kind']=='impulse':
        e=events[-1]
        expected_event=capture_impulse_event(arr_state[-1],float(A['mass_kg'][-1]),a,D['t_s'][-1]+m.tof_days*DAY_S+A['t_s'][-1])
        residual=max(float(np.linalg.norm(np.asarray(e[k])-expected_event[k])) for k in ('state_before_si','state_after_si','delta_v_vector_m_s'))
        scalar=max(abs(float(e[k])-expected_event[k]) for k in ('time_s','delta_v_m_s','mass_before_kg','mass_after_kg','propellant_kg','exhaust_velocity_m_s'))
        event_ok &= e['kind']=='arrival_impulse' and residual<1e-8 and scalar<1e-8
        event_residuals.append(dict(state_velocity_error=residual,scalar_mass_time_error=scalar))
        end_local=np.asarray(expected_event['state_after_si']);end_mass=expected_event['mass_after_kg']
    es=ep.state(m.departure,dep.metadata['epoch_jd']+D['t_s'][:-1]/DAY_S)
    ps=ep.state(m.target,m.arrival_jd+A['t_s'][1:]/DAY_S)
    expected_r=np.vstack([es[:,:3]+D['r_m'][:-1],O['r_m'],ps[:,:3]+A['r_m'][1:]])
    expected_v=np.vstack([es[:,3:]+D['v_m_s'][:-1],O['v_m_s'],ps[:,3:]+A['v_m_s'][1:]])
    expected_m=np.r_[D['mass_kg'][:-1],O['mass_kg'],A['mass_kg'][1:]]
    if a['kind']=='impulse':
        pend=ep.state(m.target,m.arrival_jd+A['t_s'][-1]/DAY_S)
        expected_r[-1]=pend[:3]+end_local[:3];expected_v[-1]=pend[3:]+end_local[3:];expected_m[-1]=end_mass
    comp_r=float(np.linalg.norm(J['r_m']-expected_r,axis=1).max());comp_v=float(np.linalg.norm(J['v_m_s']-expected_v,axis=1).max())
    comp_m=float(np.max(abs(J['mass_kg']-expected_m)))
    expected_t=np.r_[D['t_s'][:-1],D['t_s'][-1]+O['t_s'],D['t_s'][-1]+m.tof_days*DAY_S+A['t_s'][1:]]
    comp_t=float(np.max(abs(J['t_s']-expected_t)))
    thrust=np.r_[D['thrust_N'][:-1],O['thrust_N'],A['thrust_N'][1:]]
    flags=np.r_[D['active'][:-1],O['active'],A['active'][1:]]
    composition=comp_r<.001 and comp_v<1e-8 and comp_m<1e-6 and comp_t<1e-6 and np.array_equal(J['thrust_N'],thrust) and np.array_equal(J['active'],flags)
    final_elements=elements(end_local,orbit.mu_m3_s2)
    orbit_error=max(abs(final_elements['periapsis_radius_m']-orbit.planet_radius_m-orbit.periapsis_altitude_m),
                    abs(final_elements['apoapsis_radius_m']-orbit.planet_radius_m-orbit.apoapsis_altitude_m))
    min_clearance=float(np.min(np.linalg.norm(A['r_m'],axis=1))-orbit.planet_radius_m)
    if a['kind']=='spiral':min_clearance=min(min_clearance,float(replay['minimum_radius_m'])-orbit.planet_radius_m)
    outer_check=verify_bounded(outer);vendor=verify_kiam_psi(outer)
    from .capture_control import capture_budget_check
    budget=capture_budget_check(a,m.mass_kg,float(A['mass_kg'][0]),end_mass,float(A['t_s'][-1])) if a['kind']=='spiral' else dict(passed=True)
    passed=(audit['passed'] and outer_check['passed'] and vendor['passed'] and links and composition and circular and interface_radii and phase_times and dep_ok
            and left_r<.1 and left_v<1e-6 and left_m<1e-6 and right_r<.001 and right_v<1e-8 and right_m<1e-6
            and time_error<1e-4 and departure_mass_flow<1e-6 and arrival_flow<1e-6 and thrust_ok
            and arr_r<100. and arr_v<.01 and arr_m<1e-6 and event_ok and orbit_error<m.position_tolerance_m
            and float(J['mass_kg'].min())>=dry-1e-6 and min_clearance>=orbit.periapsis_altitude_m-1000. and budget['passed'])
    return dict(passed=bool(passed),kind='four_orbital_modes',departure_kind=d['kind'],arrival_kind=a['kind'],
                departure_join=dict(position_error_m=left_r,velocity_error_m_s=left_v,mass_error_kg=left_m),
                arrival_join=dict(position_error_m=right_r,velocity_error_m_s=right_v,mass_error_kg=right_m),
                time_error_s=time_error,composition_position_error_m=comp_r,composition_velocity_error_m_s=comp_v,
                composition_mass_error_kg=comp_m,composition_time_error_s=comp_t,source_links_passed=bool(links),
                departure_replay=dep_check,arrival_replay=dict(position_error_m=arr_r,velocity_error_m_s=arr_v,mass_error_kg=arr_m),
                events_passed=bool(event_ok),impulse_residuals=event_residuals,orbit_element_error_m=orbit_error,
                initial_orbit_mass_kg=m.mass_kg,interplanetary_initial_mass_kg=float(O['mass_kg'][0]),final_mass_kg=end_mass,
                departure_propellant_kg=float(D['mass_kg'][0]-D['mass_kg'][-1]),interplanetary_propellant_kg=float(O['mass_kg'][0]-O['mass_kg'][-1]),
                arrival_propellant_kg=float(A['mass_kg'][0]-end_mass),total_spacecraft_propellant_kg=float(m.mass_kg-end_mass),
                departure_mass_flow_error_kg=departure_mass_flow,arrival_mass_flow_error_kg=arrival_flow,
                capture_budget=budget,outer_verification=outer_check,kiam_verification=vendor,
                scope='Patched central fields; prescribed transverse spirals or explicit impulse events; external upper-stage mass excluded, no global optimality claim')
