"""Date-first IRT with explicit fallback, separate budgets and truthful provenance."""
from dataclasses import replace
import numpy as np
from .coordinate_matrix import phase_seed, timed_call
from .iltt_entry import resolve_date_mission, date_entry
from .irt import solve_irt
from .verification import verify_irt
from .contract import audit_configuration, make_request


def resolve_with_fallback(mission):
    """Return a date-derived context, never fit a branch to a requested duration."""
    if not date_entry(mission):
        return mission
    try:
        return timed_call(float(mission.solver.get('iltt_budget_s',60)),resolve_date_mission,mission)
    except (ValueError, RuntimeError, TimeoutError, OverflowError, np.linalg.LinAlgError) as exc:
        resolved,p,record=phase_seed(mission)
        bounds=mission.solver.get('iltt_duration_bounds_days')
        if bounds and not bounds[0]<=resolved.tof_days<=bounds[1]:
            raise ValueError('Date-derived fallback duration outside declared horizon') from exc
        record.update(entry_error=str(exc),costates=p.tolist(),accepted_iltt=False)
        return replace(resolved,solver=dict(resolved.solver,irt_date_fallback=record))


def solve_entry(mission):
    resolved=resolve_with_fallback(mission)
    fallback=resolved.solver.get('irt_date_fallback')
    if fallback:
        seed=np.asarray(fallback['costates']);reference=fallback['parameters']
    elif date_entry(resolved):
        entry=resolved.solver['iltt_resolved'];seed=np.asarray(entry['costates']);reference=entry['x_corrected']
    else:
        return resolved,*solve_irt(resolved)
    configured=resolved.solver.get('irt_coordinates','costates')
    modes=list(configured) if isinstance(configured,(list,tuple)) else [configured]
    for mode in ('iltt','costates'):
        if mode not in modes:modes.append(mode)
    # Costates get a distinct recovery attempt after a failed ILTT chart.
    if modes[-1]!='costates':modes.append('costates')
    history=[]
    for index,mode in enumerate(modes):
        budget=float(resolved.solver.get('irt_coordinate_budget_s',resolved.solver.get('budget_s',60)))
        trial=replace(resolved,solver=dict(resolved.solver,irt_coordinates=mode,iltt_coordinate_reference=reference,
                                         budget_s=budget,attempt_budget_s=budget))
        event=dict(coordinates=mode,accepted=False)
        try:
            result,diag=timed_call(budget+2,solve_irt,trial,costate_seed=seed)
            event['diagnostics']=diag
            if result is not None and verify_irt(result)['passed']:
                audit_configuration(result,trial,make_request(trial))
                result.metadata['entry_route']=dict(accepted_iltt=not bool(fallback),fallback=fallback,coordinates=mode)
                result.metadata['chosen_seed']['source']='ILTT date/phase approximation' if fallback else 'ILTT date/phase'
                event['accepted']=True;history.append(event)
                return trial,result,dict(coordinate_steps=history,entry_route=result.metadata['entry_route'])
            last=[a['last_costates'] for a in diag.get('attempts',[]) if 'last_costates' in a]
            if last:seed=np.asarray(last[-1])
        except (ValueError,RuntimeError,TimeoutError,OverflowError,np.linalg.LinAlgError) as exc:
            event['error']=str(exc)
        history.append(event)
    return resolved,None,dict(coordinate_steps=history,entry_route=dict(accepted_iltt=not bool(fallback),fallback=fallback))
