"""Correct a verified IRT onto another explicitly selected orbit source."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import numpy as np
from .data import Trajectory, Scales, write_json
from .problem import Mission
from .irt import solve_irt
from .verification import verify_irt
from .contract import make_request, audit_configuration, stamp_configuration


def reconcile_irt(source, orbit_sources, output, *, coordinates=None):
    if source.metadata.get('stage')!='irt' or not verify_irt(source)['passed']:
        raise ValueError('Source transition requires a verified IRT without departure excess')
    old=Mission(**source.metadata['mission']).validate()
    if old.center.lower()!='sun' or any(getattr(old,k) is not None for k in ('lunar','capture','parking_departure','orbital_maneuvers','arrival_offset_state_si','departure_offset_state_si')):
        raise ValueError('Source transition currently supports central body-to-body IRT')
    audit_configuration(source,old,make_request(old))
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    settings={k:v for k,v in old.solver.items() if k!='iltt_resolved'}
    settings['irt_entry']='fixed_time';settings['compare_seeds']=False
    if coordinates is not None:settings['irt_coordinates']=coordinates
    reference=old.solver.get('iltt_coordinate_reference',old.solver.get('iltt_resolved',{}).get('x_corrected'))
    if reference is not None:settings['iltt_coordinate_reference']=reference
    mission=replace(old,orbit_sources=orbit_sources,solver=settings).validate()
    old_eph,new_eph=old.ephemerides(),mission.ephemerides()
    initial,target,_=mission.boundary()
    before=np.asarray(source.metadata['target_state_si'])
    summary=dict(status='partial',stage='orbit_source_transition',from_sources=old.orbit_sources,
                 to_sources=orbit_sources,launch_tdb=mission.launch_tdb,tof_days=mission.tof_days,
                 initial_shift_m=float(np.linalg.norm(initial[:3]-np.asarray(source.metadata['initial_state_si'])[:3])),
                 target_shift_m=float(np.linalg.norm(target[:3]-before[:3])),
                 target_shift_m_s=float(np.linalg.norm(target[3:]-before[3:])),attempts=[])
    write_json(root/'request.json',make_request(mission))
    write_json(root/'source.json',source.metadata)
    # First try the whole correction; reduce only on a numerical failure.
    alpha=0.;step=1.;current=source
    for _ in range(20):
        trial=min(1.,alpha+step)
        class Blend:
            def state(self,body,jd,center='Sun'):
                return (1-trial)*old_eph.state(body,jd,center)+trial*new_eph.state(body,jd,center)
            def coverage(self,body):
                a,b=old_eph.coverage(body),new_eph.coverage(body)
                return dict(source='boundary_homotopy',alpha=trial,from_source=a,to_source=b,
                            start_jd=max(a['start_jd'],b['start_jd']),stop_jd=min(a['stop_jd'],b['stop_jd']))
        eph=new_eph if trial==1 else Blend()
        # Rescale the last accepted guess for the current departure normalization.
        _,_,scale=mission.boundary(eph)
        prior=Scales(**current.metadata['scales'])
        guess=np.asarray(current.metadata['costates_initial']).copy()
        factor=prior.acceleration_m_s2/scale.acceleration_m_s2
        guess[3:]*=factor;guess[:3]*=factor*scale.time_s/prior.time_s
        try:
            result,diag=solve_irt(mission,eph,costate_seed=guess)
        except (ValueError,RuntimeError,TimeoutError,np.linalg.LinAlgError) as exc:
            result,diag=None,dict(status='failed',error=str(exc))
        row=dict(alpha=trial,diagnostics=diag,accepted=False)
        if result is not None:
            check=verify_irt(result);row.update(accepted=check['passed'],verification=check)
        summary['attempts'].append(row)
        if row['accepted']:
            alpha=trial;current=result
            if trial==1:
                audit_configuration(result,mission,make_request(mission));stamp_configuration(result)
                summary.update(status='completed_stage',last_result='irt',verification=check,reached_alpha=1.)
                result.metadata.update(status='verified_extremal',verification=check,
                                       orbit_source_transition=deepcopy(summary))
                result.save(root/'irt')
                summary.update(status='completed_stage',last_result='irt',verification=check)
                break
            step=min(1-alpha,step*1.5)
        else:
            step*=.5
            if step<1/128:break
        summary['reached_alpha']=alpha
        write_json(root/'summary.json',summary)
    summary['reached_alpha']=alpha
    write_json(root/'summary.json',summary)
    return (current if alpha==1 else None),summary
