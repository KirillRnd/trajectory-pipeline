"""Physical constant-exhaust transition, retaining optimal departure conditions."""
from pathlib import Path
from time import perf_counter
from .data import Scales,Trajectory,write_json
from .bounded_model import BoundedModel
from .bounded import canonical,assemble,verify_bounded,collocate
from .bangbang import solve_bangbang
from .continuation import continue_parameter


def run_psi(source,output,*,resume=False):
    from .contract import audit_configuration
    audit_configuration(source)
    if source.metadata.get('stage') not in ('pazov','pazov_limit') or source.metadata['status']!='verified_extremal':
        raise ValueError('Physical PSI transition requires a verified Pazov-stage result')
    output=Path(output)
    output.mkdir(parents=True,exist_ok=resume)
    mission=source.metadata['mission']
    scales=Scales(**source.metadata['scales'])
    spacecraft=mission['spacecraft']
    thrust,exhaust,dry=float(spacecraft['thrust_N']),float(spacecraft['exhaust_velocity_m_s']),float(spacecraft['dry_mass_kg'])
    if thrust<=0 or exhaust<=0 or not 0<dry<mission['mass_kg']:
        raise ValueError('Invalid thrust, exhaust velocity or dry mass')
    actual=thrust/mission['mass_kg']/scales.acceleration_m_s2
    bridge_a=float(source.metadata['bounded_model']['a_max'])
    if bridge_a<actual*(1-1e-9):
        raise ValueError('Source thrust bound is below the specified hardware value')
    q=bridge_a*scales.velocity_m_s/exhaust
    old_alpha=source.metadata['bounded_model']['alpha']
    settings=mission['solver']
    bridge_alpha=float(settings.get('psi_mass_alpha',.5))
    alpha=min(old_alpha,bridge_alpha) if old_alpha>0 else bridge_alpha
    if not 0<alpha<1:raise ValueError('Mass bridge requires a mixed-functional alpha in (0,1)')
    attempt=float(settings.get('bounded_attempt_s',20))
    base=dict(mission=mission,source_arrays_sha256=source.metadata.get('arrays_sha256'),
              a_max=actual,bridge_a_max=bridge_a,q=q,min_step=1e-4,max_step=.2)
    def make_model(a,**options):return BoundedModel(a,gravity_spec=source.metadata.get('gravity_spec'),**options)
    def bounded_correct(previous,model,deadline,stage):
        return collocate(source,previous,model,min(deadline,perf_counter()+attempt),stage)
    if old_alpha!=alpha:
        def regularize(s,previous,deadline):
            return bounded_correct(previous,make_model(bridge_a,alpha=old_alpha+(alpha-old_alpha)*s),deadline,'pazov')
        regularized,state=continue_parameter(source,output/'regularize',regularize,
                     profile=dict(base,stage='psi_regularize',budget_s=settings.get('psi_budget_s',180)),
                     resume=resume and (output/'regularize/continuation.json').exists(),initial_step=1.)
        if state['status']!='completed_stage':
            summary=dict(status='partial',phase='regularize',last_result='regularize/'+state['last_point'])
            write_json(output/'summary.json',summary)
            return regularized,summary
    else:regularized=source
    initial_model=make_model(bridge_a,alpha=alpha,beta=0.,q=q,variable_mass=True)
    times=regularized.arrays['t_s']/scales.time_s
    face='active' if regularized.metadata['departure']['bound_active'] else 'free'
    initial=assemble(regularized,initial_model,times,canonical(regularized,initial_model),face,'psi_mass')
    check=verify_bounded(initial)
    if not check['passed']:raise ValueError('Variable-mass bridge at beta=0 failed: '+str(check))
    initial.metadata.update(status='verified_extremal',verification=check)
    def add_mass(s,previous,deadline):
        return bounded_correct(previous,make_model(bridge_a,alpha=alpha,beta=s,q=q,variable_mass=True),deadline,'psi_mass')
    mass_state,state=continue_parameter(initial,output/'mass',add_mass,
                profile=dict(base,stage='psi_mass',alpha=alpha,budget_s=settings.get('psi_budget_s',180)),
                resume=resume and (output/'mass/continuation.json').exists())
    if state['status']!='completed_stage':
        summary=dict(status='partial',phase='mass',reached_beta=state['reached_parameter'],
                     last_result='mass/'+state['last_point'])
        write_json(output/'summary.json',summary)
        return mass_state,summary
    if bridge_a>actual*(1+1e-9):
        # The constant-mass surrogate can be more restrictive than the physical
        # spacecraft, whose available acceleration grows as fuel is expended.
        # Introduce mass first, then reach the actual fixed thrust. Intermediate
        # larger thrust values remain explicitly marked as homotopy states.
        def reduce_force(s,previous,deadline):
            a=bridge_a+(actual-bridge_a)*s
            return bounded_correct(previous,make_model(a,alpha=alpha,beta=1.,q=a*scales.velocity_m_s/exhaust,variable_mass=True),deadline,'psi_limit')
        mass_state,state=continue_parameter(mass_state,output/'limit',reduce_force,
                    profile=dict(base,stage='psi_limit',alpha=alpha,budget_s=settings.get('psi_budget_s',180)),
                    resume=resume and (output/'limit/continuation.json').exists())
        if state['status']!='completed_stage':
            summary=dict(status='partial',phase='physical_thrust_limit',hardware_limit_reached=False,
                         reached_parameter=state['reached_parameter'],last_result='limit/'+state['last_point'])
            write_json(output/'summary.json',summary)
            return mass_state,summary
    q=actual*scales.velocity_m_s/exhaust
    last_bang_seed=None
    def linearize(s,previous,deadline):
        nonlocal last_bang_seed
        model=make_model(actual,alpha=alpha+(1-alpha)*s,beta=1.,q=q,variable_mass=True)
        exact_deadline=min(deadline,perf_counter()+float(settings.get('exact_attempt_s',60. if model.gravity is not None else attempt)))
        deadline=min(deadline,perf_counter()+attempt)
        if s==1:return solve_bangbang(source,previous,model,exact_deadline,'psi')
        seed=tuple(previous.metadata['costates_initial'])
        if model.alpha>=.975 and seed!=last_bang_seed:
            last_bang_seed=seed
            try:
                exact=solve_bangbang(source,previous,make_model(actual,alpha=1.,beta=1.,q=q,variable_mass=True),exact_deadline,'psi')
                exact.metadata['_continuation_target_reached']=True
                return exact
            except (ValueError,RuntimeError):
                pass
        return collocate(source,previous,model,deadline,'psi')
    result,state=continue_parameter(mass_state,output/'fuel',linearize,
                profile=dict(base,stage='psi_fuel',start_alpha=alpha,budget_s=settings.get('psi_budget_s',180)),
                resume=resume and (output/'fuel/continuation.json').exists())
    summary=dict(status=state['status'],phase='fuel',reached_alpha=alpha+(1-alpha)*state['reached_parameter'],
                 last_result='fuel/'+state['last_point'],verification=result.metadata.get('verification'))
    write_json(output/'summary.json',summary)
    return result,summary
