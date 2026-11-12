"""Adaptive continuation with immutable accepted points and restart checkpoints."""
from pathlib import Path
import json
import math
from time import perf_counter
from datetime import datetime,timezone
from .data import Trajectory, write_json,sha256


def _compatible_profile(old,new):
    old,new=dict(old),dict(new)
    if 'bridge_a_max' in old or 'bridge_a_max' in new:
        old.setdefault('bridge_a_max',old.get('a_max'))
        new.setdefault('bridge_a_max',new.get('a_max'))
    for key in ('a_max','q','bridge_a_max'):
        if key in old and key in new:
            if not math.isclose(old.pop(key),new.pop(key),rel_tol=1e-12,abs_tol=1e-15):return False
    return old==new


def continue_parameter(initial, output, correct, *, profile, resume=False,initial_step=None):
    output=Path(output)
    if resume:
        checkpoint=json.loads((output/'continuation.json').read_text(encoding='utf-8'))
        if not _compatible_profile(checkpoint['profile'],profile):
            raise ValueError('Resume configuration/source differs from checkpoint')
        current=Trajectory.load(output/checkpoint['last_point'])
        parameter=float(checkpoint['reached_parameter'])
        step=float(checkpoint['next_step'])
        history=checkpoint['history']
    else:
        output.mkdir(parents=True,exist_ok=False)
        initial.save(output/'initial')
        current,parameter,step,history=initial,0.,(.2 if initial_step is None else float(initial_step)),[]
        checkpoint=dict(profile=profile,last_point='initial')
    begin=perf_counter()
    minimum=float(profile.get('min_step',.001))
    maximum=float(profile.get('max_step',.25))
    budget=float(profile.get('budget_s',90))
    if resume:
        step=max(minimum,step)
        if parameter==0 and initial_step is not None:step=max(step,float(initial_step))
    status='partial'
    root=Path(__file__).resolve().parents[1]
    sources={p.relative_to(root).as_posix():sha256(p) for p in sorted((root/'trajectory_pipeline').glob('*.py'))}
    sources['ILTT/continuation_methods.py']=sha256(root/'ILTT/continuation_methods.py')
    checkpoint.setdefault('sessions',[]).append(dict(started_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sources))
    checkpoint.update(status=status,reached_parameter=parameter,next_step=step,history=history)
    write_json(output/'continuation.json',checkpoint)
    attempts_session=0
    while parameter<1-1e-12 and attempts_session<150:
        if perf_counter()-begin>budget:
            break
        trial=min(1.,parameter+step)
        event=dict(parameter=trial,step=step)
        try:
            candidate=correct(trial,current,begin+budget)
            candidate.validate()
            accepted_parameter=1. if candidate.metadata.pop('_continuation_target_reached',False) else trial
            index=len(history)
            destination=output/f'point_{index:04d}'
            while destination.exists():
                index+=1
                destination=output/f'point_{index:04d}'
            candidate.save(destination)
            current,parameter=candidate,accepted_parameter
            checkpoint['last_point']=destination.name
            event['accepted']=True
            event['accepted_parameter']=accepted_parameter
            step=min(maximum,step*1.5)
        except (ValueError,RuntimeError,TimeoutError) as exc:
            event.update(accepted=False,message=f'{type(exc).__name__}: {exc}')
            step*=.5
        except Exception as exc:
            checkpoint.update(status='failed',error=f'{type(exc).__name__}: {exc}',
                              reached_parameter=parameter,next_step=step,history=history)
            write_json(output/'continuation.json',checkpoint)
            raise
        history.append(event)
        attempts_session+=1
        checkpoint.update(status='completed_stage' if parameter>=1-1e-12 else 'partial',
                          reached_parameter=parameter,next_step=step,history=history,
                          elapsed_s_current_session=perf_counter()-begin)
        write_json(output/'continuation.json',checkpoint)
        if not event['accepted'] and step<minimum:
            break
    status='completed_stage' if parameter>=1-1e-12 else 'partial'
    checkpoint.update(status=status,reached_parameter=parameter,next_step=step,history=history,
                      elapsed_s_current_session=perf_counter()-begin,attempts_current_session=attempts_session,
                      stop_reason='target_reached' if status=='completed_stage' else
                                  'minimum_step' if step<minimum else
                                  'attempt_budget' if attempts_session>=150 else 'time_budget')
    write_json(output/'continuation.json',checkpoint)
    return current,checkpoint
