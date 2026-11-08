"""Connect verified departure solutions to the local Pazov control law."""
from copy import deepcopy
from pathlib import Path
from time import perf_counter
import numpy as np
from .data import Scales,Trajectory,write_json
from .bounded_model import BoundedModel
from .bounded import canonical,assemble,verify_bounded,collocate
from .bangbang import solve_bangbang
from .continuation import continue_parameter


def run_pazov(source,output,*,target_alpha=1.,resume=False):
    from .contract import audit_configuration
    audit_configuration(source)
    if source.metadata.get('stage') not in ('departure','irt') or source.metadata['status']!='verified_extremal':
        raise ValueError('Pazov transition requires a verified IRT/departure solution')
    if not 0<target_alpha<=1:raise ValueError('target_alpha must be in (0,1]')
    output=Path(output)
    output.mkdir(parents=True,exist_ok=resume)
    mission=source.metadata['mission']
    scales=Scales(**source.metadata['scales'])
    thrust=float(mission['spacecraft']['thrust_N'])
    if not thrust>0:raise ValueError('Spacecraft thrust must be positive')
    actual=thrust/mission['mass_kg']/scales.acceleration_m_s2
    peak=float(np.linalg.norm(source.arrays['acceleration_m_s2'],axis=1).max()/scales.acceleration_m_s2)
    start=max(actual,peak*1.03)
    def make_model(a,alpha=0.):return BoundedModel(a,alpha=alpha,gravity_spec=source.metadata.get('gravity_spec'))
    face='active' if source.metadata.get('departure',{}).get('bound_active',True) else 'free'
    times=source.arrays['t_s']/scales.time_s
    initial=assemble(source,make_model(start),times,canonical(source,make_model(start)),face,'pazov_limit')
    initial_check=verify_bounded(initial)
    if not initial_check['passed']:raise ValueError('Initial bounded quadratic conversion failed: '+str(initial_check))
    initial.metadata.update(status='verified_extremal',verification=initial_check)
    attempt_budget=float(mission['solver'].get('bounded_attempt_s',15))
    base=dict(mission=mission,source_arrays_sha256=source.metadata.get('arrays_sha256'),
              target_a_max=actual,min_step=1e-4,max_step=.2)
    if start>actual*(1+1e-12):
        profile=dict(base,stage='pazov_limit',budget_s=mission['solver'].get('limit_budget_s',90))
        def correct_limit(s,previous,deadline):
            return collocate(source,previous,make_model(start+(actual-start)*s),
                              min(deadline,perf_counter()+attempt_budget),'pazov_limit')
        limited,state=continue_parameter(initial,output/'limit',correct_limit,profile=profile,
                                         resume=resume and (output/'limit/continuation.json').exists())
        last_path='limit/'+state['last_point']
        if state['status']!='completed_stage':
            summary=dict(status='partial',phase='thrust_limit',hardware_limit_reached=False,
                         reached_parameter=state['reached_parameter'],last_result=last_path)
            write_json(output/'summary.json',summary)
            return limited,summary
    else:
        if resume and (output/'limit/trajectory.json').exists():limited=Trajectory.load(output/'limit')
        else:
            initial.save(output/'limit')
            limited=initial
        last_path='limit'
    profile=dict(base,stage='pazov_functional',target_alpha=target_alpha,
                 budget_s=mission['solver'].get('pazov_budget_s',150))
    def correct_functional(s,previous,deadline):
        alpha=target_alpha*s
        model=make_model(actual,alpha=alpha)
        deadline=min(deadline,perf_counter()+attempt_budget)
        if alpha==1:return solve_bangbang(source,previous,model,deadline,'pazov')
        return collocate(source,previous,model,deadline,'pazov')
    result,state=continue_parameter(limited,output/'functional',correct_functional,profile=profile,
                                    resume=resume and (output/'functional/continuation.json').exists())
    summary=dict(status=state['status'],phase='mixed_functional',hardware_limit_reached=True,
                 target_alpha=target_alpha,reached_alpha=state['reached_parameter']*target_alpha,
                 last_result='functional/'+state['last_point'],verification=result.metadata.get('verification'))
    write_json(output/'summary.json',summary)
    return result,summary
