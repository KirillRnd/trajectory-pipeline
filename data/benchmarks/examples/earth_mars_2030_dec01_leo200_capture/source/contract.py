"""Check the requested mission against stage metadata and dimensional physics.

The hash binds resolved parameters, not a self-reported hardware flag. Final
admission also reconstructs F and c from normalized equations and profiles.
"""
import hashlib
import json
import numpy as np
from .data import Scales,DAY_S
from .problem import Mission
from .ephemerides import canonical


def _raw_specification(mission):
    mission=mission if isinstance(mission,Mission) else Mission(**mission)
    result=mission.validate().to_dict()
    result.pop('solver')
    return result


def specification(mission):
    result=_raw_specification(mission)
    for key in ('tof_days','position_tolerance_m','velocity_tolerance_m_s','mass_kg','vinf_max_m_s'):
        result[key]=float(result[key])
    result['spacecraft']={key:float(value) for key,value in result['spacecraft'].items()}
    if result['vinf_vector_m_s'] is not None:result['vinf_vector_m_s']=[float(value) for value in result['vinf_vector_m_s']]
    if 'arrival_offset_state_si' in result:result['arrival_offset_state_si']=[float(x) for x in result['arrival_offset_state_si']]
    if 'departure_offset_state_si' in result:result['departure_offset_state_si']=[float(x) for x in result['departure_offset_state_si']]
    if 'parking_departure' in result:result['parking_departure']={k:float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) else v for k,v in result['parking_departure'].items()}
    if 'capture' in result:
        result['capture']={k:float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) else v for k,v in result['capture'].items()}
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()


def configuration_hash(mission):
    return digest(specification(mission))


def make_request(mission):
    initial,target,scales=mission.boundary()
    payload=dict(schema_version=1,configuration_hash_version=2,mission=specification(mission),configuration_sha256=configuration_hash(mission),
                 epoch_jd=mission.launch_jd,tof_s=mission.tof_days*DAY_S,
                 frame='ECLIPJ2000',time_scale='TDB',center=mission.center,
                 body_initial_state_si=initial.tolist(),target_state_si=target.tolist(),
                 scales=dict(distance_m=scales.distance_m,mu_m3_s2=scales.mu_m3_s2))
    return dict(payload,request_sha256=digest(payload))


def audit_configuration(trajectory,expected=None,request=None,require_final=False):
    meta,a=trajectory.metadata,trajectory.arrays
    actual=Mission(**meta['mission']).validate()
    expected=actual if expected is None else expected
    expected=expected if isinstance(expected,Mission) else Mission(**expected)
    wanted=specification(expected);observed=specification(actual)
    errors=[]
    for key in wanted:
        if wanted[key]!=observed[key]:errors.append('mission.'+key)
    identity=configuration_hash(expected)
    stamps={configuration_hash(actual),digest(_raw_specification(actual))}
    if meta.get('configuration_sha256',configuration_hash(actual)) not in stamps:errors.append('configuration_sha256')
    if meta.get('case_id')!=expected.case_id:errors.append('case_id')
    if canonical(meta['center'])!=canonical(expected.center):errors.append('center')
    if meta.get('frame')!='ECLIPJ2000' or meta.get('time_scale')!='TDB':errors.append('frame/time_scale')
    if not np.isclose(meta['epoch_jd'],expected.launch_jd,rtol=0,atol=1e-9):errors.append('launch epoch')
    duration=expected.tof_days*DAY_S
    if abs(a['t_s'][0])>1e-6 or not np.isclose(a['t_s'][-1],duration,rtol=1e-12,atol=1e-6):errors.append('time of flight')
    scales=Scales(**meta['scales'])
    geometry=None
    if request is not None:
        payload={k:v for k,v in request.items() if k!='request_sha256'}
        if digest(payload)!=request.get('request_sha256'):errors.append('request manifest checksum')
        request_stamps={digest(request['mission']),configuration_hash(request['mission'])}
        if request.get('mission')!=wanted or request.get('configuration_sha256') not in request_stamps:errors.append('requested configuration')
        body=np.asarray(meta.get('body_initial_state_si',meta['initial_state_si']),dtype=float).copy()
        if 'body_initial_state_si' not in meta and meta.get('departure'):
            body[3:]-=np.asarray(meta['departure']['vector_m_s'])
        target=np.asarray(meta['target_state_si'])
        ds=np.r_[np.full(3,.1),np.full(3,1e-6)]
        if np.any(np.abs(body-request['body_initial_state_si'])>ds):errors.append('departure ephemeris/boundary')
        if np.any(np.abs(target-request['target_state_si'])>ds):errors.append('arrival ephemeris/boundary')
        for key in ('distance_m','mu_m3_s2'):
            if not np.isclose(meta['scales'][key],request['scales'][key],rtol=1e-12,atol=0):errors.append('scales.'+key)
        geometry=dict(epoch_jd=request['epoch_jd'],arrival_jd=expected.arrival_jd,
                      departure_position_difference_m=float(np.linalg.norm(body[:3]-np.asarray(request['body_initial_state_si'])[:3])),
                      arrival_position_difference_m=float(np.linalg.norm(target[:3]-np.asarray(request['target_state_si'])[:3])))
    model=meta.get('bounded_model')
    hardware=expected.spacecraft
    recovered=None
    if model is not None:
        if not np.isfinite(model['a_max']) or model['a_max']<=0:
            raise ValueError('Configuration mismatch: invalid normalized thrust limit')
        force=model['a_max']*scales.acceleration_m_s2*expected.mass_kg
        recovered=dict(model_thrust_N=force,thrust_to_requested_ratio=force/hardware['thrust_N'],
                       alpha=model['alpha'],beta=model['beta'],variable_mass=model['variable_mass'])
        reached=bool(np.isclose(force,hardware['thrust_N'],rtol=1e-10,atol=1e-12))
        recovered['hardware_limit_reached']=reached
        if 'hardware_limit_reached' in meta and bool(meta['hardware_limit_reached'])!=reached:
            errors.append('hardware_limit_reached flag')
        if model['variable_mass']:
            if not np.isfinite(model['q']) or model['q']<=0:
                raise ValueError('Configuration mismatch: invalid mass-flow coefficient')
            exhaust=model['a_max']*scales.velocity_m_s/model['q']
            recovered['exhaust_velocity_m_s']=exhaust
            if not np.isclose(exhaust,hardware['exhaust_velocity_m_s'],rtol=1e-10,atol=1e-7):errors.append('normalized exhaust velocity / mass-flow coefficient')
            if model['beta']==1:
                if 'mass_kg' not in a or 'mass_fraction_proxy' in a:errors.append('physical mass profile')
                elif not np.isclose(a['mass_kg'][0],expected.mass_kg,rtol=1e-10,atol=1e-7):errors.append('initial mass profile')
            elif 'mass_fraction_proxy' in a and not np.isclose(a['mass_fraction_proxy'][0],1.,rtol=0,atol=1e-9):
                errors.append('initial normalized mass')
        if 'acceleration_m_s2' in a:
            fraction=(a.get('mass_kg',np.full(len(a['t_s']),expected.mass_kg))/expected.mass_kg
                      if model['beta']==1 else a.get('mass_fraction_proxy',np.ones(len(a['t_s']))))
            effective=1+model['beta']*(fraction-1)
            pv=a['costates'][:,3:6]
            direction=pv/np.maximum(np.linalg.norm(pv,axis=1)[:,None],1e-15)
            predicted=(model['a_max']*scales.acceleration_m_s2*a['throttle']/effective)[:,None]*direction
            if not np.allclose(a['acceleration_m_s2'],predicted,rtol=1e-9,atol=1e-12):errors.append('acceleration/thrust/mass profile')
        if require_final:
            if not (model['variable_mass'] and model['alpha']==1 and model['beta']==1):errors.append('final physical model')
            if not np.isclose(force,hardware['thrust_N'],rtol=1e-10,atol=1e-12):errors.append('final thrust differs from requested hardware')
            if 'mass_kg' in a:
                if np.min(a['mass_kg'])<hardware['dry_mass_kg']-1e-5:errors.append('dry mass constraint')
            if 'thrust_N' not in a or not np.allclose(a.get('thrust_N'),hardware['thrust_N']*a['throttle'],rtol=1e-10,atol=1e-12):
                errors.append('requested thrust profile')
            if 'mass_kg' in a and 'switch_times_s' in meta:
                durations=np.diff(np.r_[0,meta['switch_times_s'],duration])
                flags=np.where(np.arange(len(durations))%2==0,meta['initial_throttle'],1-meta['initial_throttle'])
                used=hardware['thrust_N']/hardware['exhaust_velocity_m_s']*float(durations@flags)
                if abs(expected.mass_kg-a['mass_kg'][-1]-used)>1e-4:errors.append('requested F/c fuel balance')
    elif require_final:errors.append('missing physical model')
    if errors:raise ValueError('Configuration mismatch: '+', '.join(errors))
    return dict(passed=True,configuration_sha256=identity,configuration_hash_version=2,
                requested=dict(mass_kg=expected.mass_kg,**hardware,launch_tdb=expected.launch_tdb,
                               tof_days=expected.tof_days,departure=expected.departure,target=expected.target,mode=expected.mode),
                recovered_model=recovered,geometry=geometry,final_admission=bool(require_final))


def stamp_configuration(trajectory):
    audit_configuration(trajectory)
    trajectory.metadata['configuration_sha256']=configuration_hash(trajectory.metadata['mission'])
    trajectory.metadata['configuration_hash_version']=2
    return trajectory
