"""One recorded continuation attempt in isolation; never an acceptance sweep."""
from dataclasses import asdict,replace
from pathlib import Path
from time import perf_counter
import json
import os
import sys
import traceback
import numpy as np
from .data import Trajectory,Scales,DAY_S,write_json,sha256
from .problem import Mission
from .bounded_model import BoundedModel
from .bounded import collocate
from .contract import audit_configuration
from .runtime import runtime_environment


def prepare_step(case,phase):
    case=Path(case)
    mission=Mission.load(case/'mission.json')
    request=json.loads((case/'request.json').read_text(encoding='utf-8'))
    folder=case/'stage_psi'/phase
    checkpoint=json.loads((folder/'continuation.json').read_text(encoding='utf-8'))
    previous=Trajectory.load(folder/checkpoint['last_point'])
    source=Trajectory.load(case/'psi_source')
    audit_configuration(source,mission,request)
    audit_configuration(previous,mission,request)
    model=BoundedModel(**previous.metadata['bounded_model'])
    trial=min(1.,checkpoint['reached_parameter']+checkpoint['next_step'])
    if trial<=checkpoint['reached_parameter']:raise ValueError('The saved continuation is already complete; there is no pending step')
    profile=checkpoint['profile']
    if phase=='fuel':
        model=replace(model,alpha=profile['start_alpha']+(1-profile['start_alpha'])*trial)
        if model.alpha>=.975:raise ValueError('This diagnostic probes smooth collocation only; exact-arc attempts require a separate recorded input')
    elif phase=='mass':model=replace(model,beta=trial)
    elif phase=='limit':
        a=profile['bridge_a_max']+(profile['a_max']-profile['bridge_a_max'])*trial
        scales=Scales(**previous.metadata['scales'])
        model=replace(model,a_max=a,q=a*scales.velocity_m_s/mission.spacecraft['exhaust_velocity_m_s'])
    else:raise ValueError('Diagnostic phase must be mass, limit or fuel')
    return mission,request,source,previous,model,trial


def diagnose_step(case,phase,output,*,budget_scale=1.,native_prefix=False):
    if not np.isfinite(budget_scale) or budget_scale<=0:raise ValueError('Diagnostic budget scale must be positive and finite')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    case=Path(case)
    mission,request,source,previous,model,trial=prepare_step(case,phase)
    original_solver=dict(source.metadata['mission']['solver'])
    settings=source.metadata['mission']['solver']
    defaults=(12.,12.) if model.gravity is not None else (4.,6.)
    for key,default in zip(('collocation_budget_s','shooting_budget_s'),defaults):
        settings[key]=float(settings.get(key,default))*budget_scale
    budget=float(settings.get('bounded_attempt_s',20))*budget_scale
    snapshot=dict(diagnostic_only=True,case=str(case),phase=phase,trial_parameter=trial,
                  mission=mission.to_dict(),previous_arrays_sha256=previous.metadata['arrays_sha256'],
                  source_arrays_sha256=source.metadata['arrays_sha256'],target_model=asdict(model),
                  budget_scale=budget_scale,original_solver=original_solver,effective_solver=settings,
                  native_prefix=native_prefix,native_imported_before='FKIAMToolbox' in sys.modules,
                  python_allocator=os.environ.get('PYTHONMALLOC','default'),
                  runtime=runtime_environment(),source_sha256={p.name:sha256(p) for p in Path(__file__).parent.glob('*.py')})
    write_json(output/'step.json',snapshot);write_json(output/'request.json',request)
    print('Recorded real continuation input',flush=True)
    if native_prefix:
        # Reproduce native ephemeris calls made for request/boundary and the
        # saved IRT overlays, without rerunning or retuning the IRT solver.
        from .ephemerides import Ephemerides
        mission.boundary();mission.boundary()
        irt=Trajectory.load(case/'stage_irt/irt')
        epochs=mission.launch_jd+irt.arrays['t_s']/DAY_S
        eph=Ephemerides()
        for body in (mission.departure,mission.target):eph.state(body,epochs,mission.center)
    snapshot['native_imported_after_prefix']='FKIAMToolbox' in sys.modules
    write_json(output/'step.json',snapshot)
    print('Starting one correction attempt',flush=True)
    started=perf_counter()
    try:
        stage={'fuel':'psi','mass':'psi_mass','limit':'psi_limit'}[phase]
        result=collocate(source,previous,model,started+budget,stage)
        result.save(output/'candidate')
        summary=dict(diagnostic_only=True,status='checked',verification=result.metadata['verification'])
    except Exception as exc:
        (output/'error.log').write_text(traceback.format_exc(),encoding='utf-8')
        summary=dict(diagnostic_only=True,status='diagnostic_stop' if isinstance(exc,(ValueError,RuntimeError,TimeoutError)) else 'program_error',
                     error=f'{type(exc).__name__}: {exc}')
    summary['elapsed_s']=perf_counter()-started
    write_json(output/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary
