from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import subprocess
import time
import traceback
import sys
from .data import write_json, sha256
from .irt import solve_irt
from .verification import verify_irt
from .problem import Mission
from .runtime import runtime_environment
from .contract import make_request,audit_configuration,stamp_configuration


def run_irt(mission, output,resume=False):
    from .irt_entry_routes import resolve_with_fallback,solve_entry
    original_mission=mission
    output = Path(output)
    output.mkdir(parents=True,exist_ok=resume)
    summary = dict(case_id=mission.case_id,status='failed',stage='irt',
                   started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version())
    summary['runtime']=runtime_environment()
    root = Path(__file__).resolve().parents[1]
    summary['source_sha256']={p.relative_to(root).as_posix():sha256(p) for p in sorted((root/'trajectory_pipeline').glob('*.py'))}
    for rel in ('ILTT/ILTTToolbox.py','ILTT/continuation_methods.py'):
        summary['source_sha256'][rel]=sha256(root/rel)
    summary['git_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    started = time.perf_counter()
    try:
        mission=resolve_with_fallback(mission)
        if resume and (output/'mission.json').exists() and Mission.load(output/'mission.json').to_dict()!=mission.to_dict():
            raise ValueError('Resume IRT mission differs from saved configuration')
        write_json(output/'mission.json',mission.to_dict())
        write_json(output/'entry_request.json',original_mission.to_dict())
        if mission.lunar is not None:
            from .lunar import solve_lunar_irt
            trajectory,diagnostics=solve_lunar_irt(mission,output,resume=resume)
        else:
            mission,trajectory,diagnostics=solve_entry(mission)
            write_json(output/'mission.json',mission.to_dict())
        write_json(output/'diagnostics.json',diagnostics)
        if trajectory is None:
            summary['status']='initial_failed'
            summary['error']='No independently verified IRT; see diagnostics.json for each attempted branch/corrector'
        else:
            check = verify_irt(trajectory)
            stamp_configuration(trajectory)
            write_json(output/'verification.json',check)
            trajectory.metadata['status']='verified_extremal' if check['passed'] else 'verification_failed'
            trajectory.metadata['verification']=check
            destination=output/'irt'
            if destination.exists():
                index=1
                while (output/f'irt_session_{index}').exists():index+=1
                destination=output/f'irt_session_{index}'
            trajectory.save(destination)
            summary.update(status='partial' if diagnostics.get('status')=='partial' else 'completed_stage' if check['passed'] else 'verification_failed',
                           last_result=destination.name,
                           verification=check,functional_dimensionless=trajectory.metadata['functional_dimensionless'])
    except Exception as exc:
        summary.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        (output/'error.log').write_text(traceback.format_exc(),encoding='utf-8')
    summary['elapsed_s']=time.perf_counter()-started
    write_json(output/'summary.json',summary)
    return summary


def sweep_irt(matrix, output):
    matrix = Path(matrix).resolve()
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    configurations = json.loads(matrix.read_text(encoding='utf-8'))
    results=[]
    for configuration in configurations:
        mission=Mission(**configuration).validate()
        print(f'{mission.case_id}: started',flush=True)
        result=run_irt(mission,output/mission.case_id)
        results.append(result)
        write_json(output/'results.json',results)
        print(f"{mission.case_id}: {result['status']}, {result['elapsed_s']:.2f} s",flush=True)
    return results


def sweep_departure(matrix, sources, output):
    from .departure import run_departure
    from .data import Trajectory
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    results=[]
    for cfg in json.loads(Path(matrix).read_text(encoding='utf-8')):
        key=cfg['case_id']
        print(f'{key}: departure started',flush=True)
        started=time.perf_counter()
        try:
            source=Trajectory.load(Path(sources)/key)
            current,checkpoint=run_departure(source,output/key)
            row=dict(case_id=key,status=checkpoint['status'],reached_parameter=checkpoint['reached_parameter'],
                     last_point=checkpoint['last_point'],departure=current.metadata.get('departure'),
                     verification=current.metadata.get('verification'))
        except Exception as exc:
            row=dict(case_id=key,status='failed',error=f'{type(exc).__name__}: {exc}')
        row['elapsed_s']=time.perf_counter()-started
        results.append(row)
        write_json(output/'results.json',results)
        print(f"{key}: {row['status']}, {row['elapsed_s']:.2f} s",flush=True)
    return results


def sweep_pipeline(matrix,output,resume=False,pending_only=False,parameter_design=None):
    """Run unchanged common pipeline rules on a declared real-mission matrix."""
    from .data import Trajectory
    output=Path(output)
    configurations=json.loads(Path(matrix).read_text(encoding='utf-8'))
    missions=[Mission(**cfg).validate() for cfg in configurations]
    if parameter_design is not None:
        from .parameter_study import build_matrix
        if [m.to_dict() for m in missions]!=build_matrix(parameter_design):
            raise ValueError('Parameter matrix differs from its declared design; no cases launched')
    ids=[m.case_id for m in missions]
    if len(ids)!=len(set(ids)):raise ValueError('Matrix case IDs must be unique')
    output.mkdir(parents=True,exist_ok=resume)
    manifest=[m.to_dict() for m in missions]
    environment_path=output/'environment.json'
    environment=runtime_environment()
    if resume and (output/'matrix.json').exists() and not environment_path.exists():
        raise ValueError('Legacy matrix has no environment record; start a separate Docker series')
    if resume and environment_path.exists():
        saved_environment=json.loads(environment_path.read_text(encoding='utf-8'))
        for key in ('python','system','machine','libc','dependencies','thread_limits'):
            if saved_environment.get(key)!=environment.get(key):
                raise ValueError('Matrix resume environment differs; use a new series directory')
    else:write_json(environment_path,environment)
    matrix_path=output/'matrix.json'
    if resume and matrix_path.exists():
        if json.loads(matrix_path.read_text(encoding='utf-8'))!=manifest:
            raise ValueError('Matrix resume differs from the declared mission set')
    else:write_json(matrix_path,manifest)
    if pending_only and not resume:raise ValueError('pending-only requires resume')
    existing={r['case_id']:r for r in json.loads((output/'results.json').read_text(encoding='utf-8'))} if (output/'results.json').exists() else {}
    rows=[]
    for index,mission in enumerate(missions):
        case=output/mission.case_id
        saved=json.loads((case/'summary.json').read_text(encoding='utf-8')) if (case/'summary.json').exists() else {}
        skip=pending_only and saved.get('status') in ('completed','partial','failed','initial_failed')
        if skip and mission.case_id in existing:
            rows.append(existing[mission.case_id]);continue
        print(f'{mission.case_id}: started',flush=True)
        started=time.perf_counter()
        result=None
        if skip:summary=saved
        else:
            inputs=output/'inputs';inputs.mkdir(exist_ok=True)
            config=inputs/f'{index:04d}.json';write_json(config,mission.to_dict())
            logdir=output/'worker_logs';logdir.mkdir(exist_ok=True)
            log=logdir/f'{mission.case_id}_{time.time_ns()}.log'
            command=[sys.executable,'-X','faulthandler','-m','trajectory_pipeline','solve',str(config.resolve()),'--output',str(case.resolve())]
            # A matrix is an explicit request, unlike the interactive CLI default.
            if mission.time_policy is None:command.append('--fixed-time')
            if resume and case.exists():command.append('--resume')
            settings=mission.solver
            wall_limit=(settings.get('budget_s',45)+settings.get('departure_budget_s',90)+
                        settings.get('limit_budget_s',90)+settings.get('pazov_budget_s',150)+
                        4*settings.get('psi_budget_s',180)+120)
            if mission.time_policy is not None:
                wall_limit=4*(wall_limit+settings.get('free_time_budget_s',120))
            failure=None;exitcode=None
            try:
                with log.open('w',encoding='utf-8') as stream:
                    process=subprocess.run(command,cwd=Path(__file__).resolve().parents[1],stdout=stream,stderr=subprocess.STDOUT,timeout=wall_limit)
                exitcode=process.returncode
            except subprocess.TimeoutExpired:failure=f'Worker exceeded wall-time limit {wall_limit:g} seconds'
            summary=json.loads((case/'summary.json').read_text(encoding='utf-8')) if (case/'summary.json').exists() else dict(case_id=mission.case_id,phase='initialization')
            expected=dict(completed=0,partial=2,failed=1,initial_failed=1)
            if failure is not None or summary.get('status') not in expected or exitcode!=expected.get(summary.get('status')):
                summary.update(status='failed',error=failure or f'Worker terminated without a terminal result; exit code {exitcode}',worker_log=str(log.relative_to(output)))
                case.mkdir(parents=True,exist_ok=True);write_json(case/'summary.json',summary)
            if summary['status']=='completed':result=Trajectory.load(case/'final')
        row=dict(case_id=mission.case_id,departure=mission.departure,target=mission.target,
                 mode=mission.mode,status=summary['status'],phase=summary['phase'],
                 elapsed_s=existing.get(mission.case_id,{}).get('elapsed_s',0.) if skip else time.perf_counter()-started,
                 stages={key:{k:v for k,v in value.items() if k in
                         ('status','phase','reached_parameter','reached_alpha','reached_beta','hardware_limit_reached','last_result')}
                         for key,value in summary.get('stages',{}).items()})
        if summary.get('error'):row['error']=summary['error']
        if summary.get('verification'):row['verification']=summary['verification']
        if result is not None:row['last_accepted_model']=result.metadata.get('bounded_model')
        rows.append(row)
        write_json(output/'results.json',rows)
        print(f"{mission.case_id}: {row['status']} ({row['phase']}), {row['elapsed_s']:.1f} s",flush=True)
    return rows


def _run_pipeline(mission,output,resume=False):
    """The user scenario: one mission -> accepted physical trajectory and plots."""
    from .data import Trajectory
    from .departure import run_departure
    from .pazov import run_pazov
    from .psi import run_psi
    from .bounded import verify_bounded
    from .kiam_verification import verify_kiam_psi
    from .visualization import render
    output=Path(output)
    request=make_request(mission)
    if resume:
        if Mission(**json.loads((output/'mission.json').read_text(encoding='utf-8'))).to_dict()!=mission.to_dict():
            raise ValueError('Resume mission differs from the saved pipeline configuration')
        if (output/'request.json').exists():
            saved_request=json.loads((output/'request.json').read_text(encoding='utf-8'))
            exclude={'configuration_sha256','request_sha256','configuration_hash_version'}
            if {k:v for k,v in saved_request.items() if k not in exclude}!={k:v for k,v in request.items() if k not in exclude}:
                raise ValueError('Resume request/boundary manifest differs')
            request=saved_request
        else:write_json(output/'request.json',request)
        if (output/'summary.json').exists():
            saved=json.loads((output/'summary.json').read_text(encoding='utf-8'))
            if saved.get('status')=='completed':
                final=Trajectory.load(output/'final')
                parameter_audit=audit_configuration(final,mission,request,require_final=True)
                check=verify_bounded(final)
                if not check['passed']:raise ValueError('Saved completed physical result no longer passes verification')
                kiam=verify_kiam_psi(final)
                if not kiam['passed']:raise ValueError('Saved physical result failed independent KIAM equations')
                saved['kiam_verification']=kiam
                saved['verification']=check
                saved['parameter_audit']=parameter_audit
                write_json(output/'parameter_audit.json',dict(request_sha256=request['request_sha256'],final=parameter_audit))
                if not all((output/'plots'/name).exists() for name in ('trajectory.svg','trajectory_3d.svg','profiles.svg')):
                    render(final,output/'plots')
                write_json(output/'summary.json',saved)
                return final,saved
    else:
        output.mkdir(parents=True,exist_ok=False)
        write_json(output/'mission.json',mission.to_dict())
        write_json(output/'request.json',request)
    summary=dict(case_id=mission.case_id,status='running',phase='irt',stages={})
    audits=[]
    def audit(stage,result,final=False):
        check=audit_configuration(result,mission,request,require_final=final)
        audits.append(dict(stage=stage,**check))
        write_json(output/'parameter_audit.json',dict(request_sha256=request['request_sha256'],stages=audits))
        return check
    def record(phase,result):
        summary['phase']=phase
        summary['stages'][phase]=result
        write_json(output/'summary.json',summary)
    irt_folder=output/'stage_irt'
    if resume and (irt_folder/'summary.json').exists():
        irt_summary=json.loads((irt_folder/'summary.json').read_text(encoding='utf-8'))
        if irt_summary['status']=='partial' and mission.lunar is not None:
            irt_summary=run_irt(mission,irt_folder,resume=True)
    elif mission.solver.get('irt_artifact'):
        current=Trajectory.load(mission.solver['irt_artifact'])
        audit_configuration(current,mission,request)
        if not verify_irt(current)['passed']:raise ValueError('Saved IRT seed failed replay')
        irt_folder.mkdir(parents=True)
        current.save(irt_folder/'irt')
        irt_summary=dict(status='completed_stage',last_result='irt',source=mission.solver['irt_artifact'])
        write_json(irt_folder/'summary.json',irt_summary)
    else:irt_summary=run_irt(mission,irt_folder)
    record('irt',irt_summary)
    if irt_summary['status']!='completed_stage':
        summary['status']='partial' if irt_summary['status']=='partial' else 'initial_failed'
        summary['error']=irt_summary.get('error');write_json(output/'summary.json',summary)
        return None,summary
    current=Trajectory.load(irt_folder/irt_summary.get('last_result','irt'))
    audit('irt',current)
    summary['phase']='departure';write_json(output/'summary.json',summary)
    current,checkpoint=run_departure(current,output/'stage_departure',resume=resume and (output/'stage_departure').exists())
    record('departure',dict(status=checkpoint['status'],reached_parameter=checkpoint['reached_parameter'],
                            last_result='stage_departure/'+checkpoint['last_point']))
    audit('departure',current)
    if checkpoint['status']!='completed_stage':
        summary['status']='partial';write_json(output/'summary.json',summary)
        return current,summary
    current=Trajectory.load(output/'stage_departure'/checkpoint['last_point'])
    frozen_source=output/'psi_source'
    if resume and not frozen_source.exists() and (output/'stage_psi').exists():
        # Legacy partial runs did not freeze the upstream result. Recover its
        # exact content hash before allowing any upstream continuation to move.
        checkpoints=list((output/'stage_psi').glob('*/continuation.json'))
        if checkpoints:
            profile=json.loads(checkpoints[0].read_text(encoding='utf-8'))['profile']
            digest=profile['source_arrays_sha256']
            matches=[p.parent for p in (output/'stage_pazov').rglob('trajectory.json')
                     if json.loads(p.read_text(encoding='utf-8')).get('arrays_sha256')==digest]
            if not matches:raise ValueError('Cannot recover the exact upstream input of the PSI checkpoint')
            Trajectory.load(matches[0]).save(frozen_source)
    if resume and frozen_source.exists():
        current=Trajectory.load(frozen_source)
        pazov_summary=json.loads((output/'stage_pazov/summary.json').read_text(encoding='utf-8'))
        pazov_summary=dict(pazov_summary,psi_input='psi_source',psi_input_sha256=current.metadata['arrays_sha256'])
    else:
        summary['phase']='pazov';write_json(output/'summary.json',summary)
        current,pazov_summary=run_pazov(current,output/'stage_pazov',target_alpha=float(mission.solver.get('pipeline_pazov_alpha',.5)),
                                       resume=resume and (output/'stage_pazov').exists())
        current=Trajectory.load(output/'stage_pazov'/pazov_summary['last_result'])
        current.save(frozen_source)
    record('pazov',pazov_summary)
    audit('pazov_input_to_psi',current)
    # An accepted intermediate is a legitimate smooth seed. The physical module
    # can introduce mass before finishing thrust reduction; it never labels the
    # surrogate as a final spacecraft solution.
    summary['phase']='psi';write_json(output/'summary.json',summary)
    current,psi_summary=run_psi(current,output/'stage_psi',resume=resume and (output/'stage_psi').exists())
    record('psi',psi_summary)
    audit('psi',current)
    if psi_summary['status']!='completed_stage':
        summary['status']='partial';write_json(output/'summary.json',summary)
        return current,summary
    current=Trajectory.load(output/'stage_psi'/psi_summary['last_result'])
    parameter_audit=audit('final',current,final=True)
    model=current.metadata['bounded_model']
    if not (model['variable_mass'] and model['beta']==1 and model['alpha']==1 and current.metadata['hardware_limit_reached']):
        raise RuntimeError('Physical endpoint has not reached its final model and hardware limits')
    check=verify_bounded(current)
    if not check['passed']:raise RuntimeError('Final independent verification failed: '+str(check))
    kiam=verify_kiam_psi(current)
    if not kiam['passed']:raise RuntimeError('Physical equations failed the independent KIAM cross-check')
    current.metadata['kiam_verification']=kiam
    current.metadata['parameter_audit']=parameter_audit
    if not (output/'final').exists():current.save(output/'final')
    final=Trajectory.load(output/'final')
    if final.metadata['arrays_sha256']!=current.metadata['arrays_sha256']:
        raise ValueError('Existing final artifact differs from the current accepted physical endpoint')
    render(final,output/'plots')
    summary.update(status='completed',phase='final',last_result='final',verification=check,
                   kiam_verification=kiam,parameter_audit=parameter_audit,plots='plots',arrays_sha256=final.metadata['arrays_sha256'])
    write_json(output/'summary.json',summary)
    return final,summary


def run_pipeline(mission,output,resume=False,*,release_time=False,time_bounds_days=None):
    from .iltt_entry import resolve_date_mission,date_entry
    from .irt_entry_routes import resolve_with_fallback
    from .source_pipeline import needs_source_transition,run_source_pipeline
    if needs_source_transition(mission):
        return run_source_pipeline(mission,output,resume=resume,release_time=release_time,time_bounds_days=time_bounds_days)
    original_mission=mission
    if resume and (Path(output)/'mission.json').exists():
        entry_request=Path(output)/'entry_request.json'
        saved_mission=Mission.load(Path(output)/'mission.json')
        if entry_request.exists():
            if json.loads(entry_request.read_text())!=original_mission.to_dict():raise ValueError('Resume date-first entry request differs')
            mission=saved_mission
        elif saved_mission.solver.get('date_entry_request') is not None:
            if saved_mission.solver['date_entry_request']!=original_mission.to_dict():raise ValueError('Resume date-first entry request differs')
            mission=saved_mission
    elif date_entry(mission):
        try:
            mission=resolve_with_fallback(mission)
            from dataclasses import replace
            mission=replace(mission,solver=dict(mission.solver,date_entry_request=original_mission.to_dict()))
        except Exception as exc:
            output=Path(output);output.mkdir(parents=True,exist_ok=resume)
            write_json(output/'mission.json',original_mission.to_dict())
            summary=dict(case_id=mission.case_id,status='initial_failed',phase='iltt_entry',error=type(exc).__name__+': '+str(exc))
            write_json(output/'summary.json',summary)
            return None,summary
    if release_time:
        from dataclasses import replace
        bounds=time_bounds_days or (mission.time_policy or {}).get('bounds_days')
        mission=replace(mission,time_policy=dict(bounds_days=list(bounds) if bounds is not None else [mission.tof_days*.5,mission.tof_days*1.5]))
        mission.validate()
    output=Path(output)
    owned=not output.exists()
    if resume and (output/'mission.json').exists():
        owned=Mission(**json.loads((output/'mission.json').read_text(encoding='utf-8'))).to_dict()==mission.to_dict()
    try:
        if mission.time_policy is not None:
            from .free_time import run_time_pipeline
            result,summary=run_time_pipeline(mission,output,resume=resume)
            if date_entry(original_mission):
                write_json(output/'entry_request.json',original_mission.to_dict())
                write_json(output/'iltt_entry.json',mission.solver.get('iltt_resolved',mission.solver.get('irt_date_fallback')))
            return result,summary
        if mission.orbital_maneuvers is not None:
            from .orbital_pipeline import run_orbital_pipeline
            return run_orbital_pipeline(mission,output,resume=resume)
        if mission.parking_departure is not None:
            from .launch_pipeline import run_launch_pipeline
            return run_launch_pipeline(mission,output,resume=resume)
        if mission.capture is not None:
            from .capture_pipeline import run_capture_pipeline
            return run_capture_pipeline(mission,output,resume=resume)
        result,summary=_run_pipeline(mission,output,resume=resume)
        if date_entry(original_mission):
            write_json(output/'entry_request.json',original_mission.to_dict())
            write_json(output/'iltt_entry.json',mission.solver.get('iltt_resolved',mission.solver.get('irt_date_fallback')))
        summary['completion_scope']='heliocentric_segment' if mission.center=='Sun' else 'specified_segment'
        summary['capture_included']=False
        write_json(output/'summary.json',summary)
        return result,summary
    except Exception as exc:
        if not owned or not output.exists():raise
        (output/'error.log').write_text(traceback.format_exc(),encoding='utf-8')
        path=output/'summary.json'
        summary=json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(case_id=mission.case_id,phase='initialization')
        summary.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        write_json(path,summary)
        return None,summary
