import argparse
import json
from .data import Trajectory


def exit_code(status):
    return 0 if status in ('completed','completed_stage') else 2 if status=='partial' else 1


def main():
    parser = argparse.ArgumentParser(description='Shared trajectory tools')
    sub = parser.add_subparsers(dest='command', required=True)
    search=sub.add_parser('search',help='Genetic graph search over declared dates, engines and existing routes')
    search.add_argument('mission')
    search.add_argument('--design',required=True)
    search.add_argument('--history',nargs='+',default=[])
    search.add_argument('--output',required=True)
    search.add_argument('--resume',action='store_true')
    search_worker=sub.add_parser('_search-worker',help=argparse.SUPPRESS)
    search_worker.add_argument('request')
    render = sub.add_parser('render', help='Render saved results without recalculation')
    render.add_argument('result')
    render.add_argument('--output', required=True)
    verify_orbital=sub.add_parser('verify-orbital',help='Replay saved orbital modes and verify both joins and impulse events')
    verify_orbital.add_argument('source')
    render_orbital=sub.add_parser('render-orbital',help='Render saved local maneuvers and explicit mass jumps without solving')
    render_orbital.add_argument('source')
    render_orbital.add_argument('--output',required=True)
    ref = sub.add_parser('import-reference', help='Import historical UMMP MATLAB data')
    ref.add_argument('mat_file')
    ref.add_argument('--output', required=True)
    cache = sub.add_parser('cache', help='Explicitly download local asteroid ephemerides')
    cache.add_argument('body')
    cache.add_argument('--start', required=True)
    cache.add_argument('--stop', required=True)
    cache.add_argument('--step', default='12 h')
    cache.add_argument('--refine', action='store_true')
    coverage = sub.add_parser('coverage')
    coverage.add_argument('bodies', nargs='+')
    solve = sub.add_parser('solve-irt', help='Solve and independently verify a configured real transfer')
    solve.add_argument('mission')
    solve.add_argument('--output', required=True)
    solve.add_argument('--resume',action='store_true')
    sweep = sub.add_parser('sweep-irt', help='Run a matrix of real IRT transfer configurations')
    sweep.add_argument('matrix')
    sweep.add_argument('--output', required=True)
    departure = sub.add_parser('departure', help='Continue a verified IRT result in departure excess')
    departure.add_argument('source')
    departure.add_argument('--output', required=True)
    departure.add_argument('--resume', action='store_true')
    dep_sweep = sub.add_parser('sweep-departure')
    dep_sweep.add_argument('matrix')
    dep_sweep.add_argument('--sources', required=True)
    dep_sweep.add_argument('--output', required=True)
    pazov=sub.add_parser('pazov',help='Bounded mixed-functional continuation using the local Pazov law')
    pazov.add_argument('source')
    pazov.add_argument('--output',required=True)
    pazov.add_argument('--alpha',type=float,default=1.)
    pazov.add_argument('--resume',action='store_true')
    psi=sub.add_parser('psi',help='Continue a verified Pazov solution to variable-mass constant-exhaust fuel optimum')
    psi.add_argument('source')
    psi.add_argument('--output',required=True)
    psi.add_argument('--resume',action='store_true')
    ummp=sub.add_parser('ummp',help='Continue a verified heliocentric PSI to the historical power-dependent UMMP engine')
    ummp.add_argument('source')
    ummp.add_argument('--output',required=True)
    ummp.add_argument('--resume',action='store_true')
    verify_ummp=sub.add_parser('verify-ummp',help='Independently replay a saved UMMP result or continuation point')
    verify_ummp.add_argument('source')
    pipeline=sub.add_parser('solve',help='Run the complete configured trajectory scenario and render its physical result')
    pipeline.add_argument('mission')
    pipeline.add_argument('--output',required=True)
    pipeline.add_argument('--resume',action='store_true')
    pipeline.add_argument('--tof-bounds-days',type=float,nargs=2)
    pipeline.add_argument('--fixed-time',action='store_true',help='Keep the explicitly requested flight duration')
    pipeline.add_argument('--capture-mode',choices=['continuous','angular'])
    pipeline.add_argument('--capture-half-width-deg',type=float)
    pipeline.add_argument('--capture-phase-reference',choices=['periapsis','fixed_axis'])
    pipeline.add_argument('--capture-eccentricity-slope-deg',type=float)
    pipeline.add_argument('--capture-phase-offset-deg',type=float)
    pipeline.add_argument('--capture-search-widths-deg',type=float,nargs='+')
    pipeline.add_argument('--capture-fuel-budget-kg',type=float,help='Propellant available for arrival spiral only')
    pipeline.add_argument('--spacecraft-fuel-budget-kg',type=float,help='Total spacecraft propellant, excluding external upper stage')
    pipeline.add_argument('--capture-max-days',type=float)
    physical_sweep=sub.add_parser('sweep-solve',help='Run the same complete pipeline on a declared matrix of real missions')
    physical_sweep.add_argument('matrix')
    physical_sweep.add_argument('--output',required=True)
    physical_sweep.add_argument('--resume',action='store_true')
    physical_sweep.add_argument('--pending-only',action='store_true',help='Preserve terminal first-pass outcomes and execute only unstarted cases')
    physical_sweep.add_argument('--parameter-design',help='Reject a stale/wrong parameter matrix before launching any case')
    date_sweep = sub.add_parser('sweep-psi', help='Sweep TDB dates from one PSI reference and rerun flagged cases through solve')
    date_sweep.add_argument('reference', help='Directory of a verified heliocentric PSI')
    date_sweep.add_argument('--start', required=True, help='First TDB calendar date')
    date_sweep.add_argument('--stop', required=True, help='Last allowed TDB calendar date')
    date_sweep.add_argument('--step-days', type=int, default=1)
    date_sweep.add_argument('--fast-budget-s', type=float, default=60.)
    date_sweep.add_argument('--tof-bounds-days',type=float,nargs=2)
    date_sweep.add_argument('--fixed-time',action='store_true')
    date_sweep.add_argument('--outlier-abs-kg', type=float, default=.5)
    date_sweep.add_argument('--outlier-rel', type=float, default=.05, help='Relative fuel threshold as a fraction')
    date_sweep.add_argument('--output', required=True)
    date_sweep.add_argument('--resume', action='store_true')
    matrix_report=sub.add_parser('matrix-report',help='Summarize accepted results and limits without rerunning optimization')
    matrix_report.add_argument('source')
    matrix_report.add_argument('--output',required=True)
    outcome_report=sub.add_parser('outcome-report',help='Locate exact stopped blocks and distinguish budgets, nonconvergence and errors')
    outcome_report.add_argument('source')
    outcome_report.add_argument('--output',required=True)
    diagnostic=sub.add_parser('diagnose-step',help='Replay one saved smooth continuation attempt for debugging, outside acceptance studies')
    diagnostic.add_argument('case')
    diagnostic.add_argument('--phase',choices=('mass','limit','fuel'),required=True)
    diagnostic.add_argument('--output',required=True)
    diagnostic.add_argument('--budget-scale',type=float,default=1.)
    diagnostic.add_argument('--native-prefix',action='store_true')
    matrix_compare=sub.add_parser('matrix-compare',help='Compare identical mission matrices across two recorded runs')
    matrix_compare.add_argument('first')
    matrix_compare.add_argument('second')
    matrix_compare.add_argument('--output',required=True)
    parameter_matrix=sub.add_parser('parameter-matrix',help='Build a balanced matrix from a declared variation design')
    parameter_matrix.add_argument('design')
    parameter_matrix.add_argument('--output',required=True)
    parameter_report=sub.add_parser('parameter-report',help='Audit parameters and success rates across a parameter study')
    parameter_report.add_argument('design')
    parameter_report.add_argument('source')
    parameter_report.add_argument('--output',required=True)
    args = parser.parse_args()
    if args.command=='search':
        from .search_graph import run_search
        summary=run_search(args.mission,args.design,args.history,args.output,resume=args.resume)
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0 if summary['accepted'] else 2
    if args.command=='_search-worker':
        from .search_graph import worker
        worker(args.request)
        return 0
    if args.command == 'render':
        from .visualization import render
        print(render(Trajectory.load(args.result), args.output))
    elif args.command=='verify-orbital':
        from .orbital_pipeline import verify_orbital_mission
        check=verify_orbital_mission(args.source)
        print(json.dumps(check,ensure_ascii=False,indent=2))
        return 0 if check['passed'] else 2
    elif args.command=='render-orbital':
        from .orbital_visualization import render_orbital_mission
        print(render_orbital_mission(args.source,args.output))
    elif args.command == 'import-reference':
        from .reference import import_ummp
        print(import_ummp(args.mat_file).save(args.output))
    elif args.command == 'cache':
        from .ephemerides import download, refine
        operation = refine if args.refine else download
        print(json.dumps(operation(args.body, args.start, args.stop, args.step), indent=2))
    elif args.command == 'coverage':
        from .ephemerides import Ephemerides
        eph = Ephemerides()
        for body in args.bodies:
            print(json.dumps(eph.coverage(body), ensure_ascii=False))
    elif args.command == 'solve-irt':
        from .problem import Mission
        from .runner import run_irt
        result=run_irt(Mission.load(args.mission),args.output,resume=args.resume)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return exit_code(result['status'])
    elif args.command == 'sweep-irt':
        from .runner import sweep_irt
        results=sweep_irt(args.matrix,args.output)
        return 0 if all(x['status']=='completed_stage' for x in results) else 2
    elif args.command=='departure':
        from .departure import run_departure
        result,checkpoint=run_departure(Trajectory.load(args.source),args.output,args.resume)
        print(json.dumps({k:v for k,v in checkpoint.items() if k not in ('history','sessions','profile')},ensure_ascii=False,indent=2))
        return 0 if checkpoint['status']=='completed_stage' else 2
    elif args.command=='sweep-departure':
        from .runner import sweep_departure
        results=sweep_departure(args.matrix,args.sources,args.output)
        return 0 if all(x['status']=='completed_stage' for x in results) else 2
    elif args.command=='pazov':
        from .pazov import run_pazov
        result,summary=run_pazov(Trajectory.load(args.source),args.output,target_alpha=args.alpha,resume=args.resume)
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0 if summary['status']=='completed_stage' else 2
    elif args.command=='psi':
        from .psi import run_psi
        result,summary=run_psi(Trajectory.load(args.source),args.output,resume=args.resume)
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return 0 if summary['status']=='completed_stage' else 2
    elif args.command=='ummp':
        from .ummp import run_ummp
        _,summary=run_ummp(Trajectory.load(args.source),args.output,resume=args.resume)
        print(json.dumps(summary,ensure_ascii=False,indent=2))
        return exit_code(summary['status'])
    elif args.command=='verify-ummp':
        from .ummp import verify_ummp
        check=verify_ummp(Trajectory.load(args.source))
        print(json.dumps(check,ensure_ascii=False,indent=2))
        return 0 if check['passed'] else 2
    elif args.command=='solve':
        from .problem import Mission
        from .runner import run_pipeline
        from .capture_control import apply_capture_flags
        mission=apply_capture_flags(Mission.load(args.mission),args)
        original_cli_request=mission.to_dict()
        if args.fixed_time and args.tof_bounds_days:raise ValueError('Choose free-time bounds or --fixed-time')
        if args.fixed_time:mission.time_policy=None
        elif args.tof_bounds_days or not any(x is not None for x in (mission.capture,mission.parking_departure,mission.orbital_maneuvers,mission.lunar)):
            from .iltt_entry import resolve_date_mission
            mission=resolve_date_mission(mission)
            bounds=args.tof_bounds_days or (mission.time_policy or {}).get('bounds_days')
            mission.time_policy=dict(bounds_days=bounds if bounds is not None else [mission.tof_days*.5,mission.tof_days*1.5])
        mission.validate()
        result,summary=run_pipeline(mission,args.output,resume=args.resume)
        from pathlib import Path
        from .data import write_json
        if Path(args.output).exists():
            write_json(Path(args.output)/'cli_request.json',dict(mission=original_cli_request,fixed_time=args.fixed_time,tof_bounds_days=args.tof_bounds_days))
        print(json.dumps({k:v for k,v in summary.items() if k!='stages'},ensure_ascii=False,indent=2))
        return exit_code(summary['status'])
    elif args.command=='sweep-solve':
        from .runner import sweep_pipeline
        rows=sweep_pipeline(args.matrix,args.output,resume=args.resume,pending_only=args.pending_only,parameter_design=args.parameter_design)
        return 0 if all(row['status']=='completed' for row in rows) else 2
    elif args.command == 'sweep-psi':
        from .date_sweep import run_date_sweep
        rows = run_date_sweep(args.reference, args.output, args.start, args.stop,
                              step_days=args.step_days, fast_budget_s=args.fast_budget_s,
                              outlier_abs_kg=args.outlier_abs_kg, outlier_rel=args.outlier_rel,
                              resume=args.resume,time_bounds_days=args.tof_bounds_days,fixed_time=args.fixed_time)
        return 0 if all(row['status'] == 'completed' for row in rows) else 2
    elif args.command=='matrix-report':
        from .matrix_report import report_matrix
        result=report_matrix(args.source,args.output)
        print(json.dumps({k:v for k,v in result.items() if k not in ('rows','details')},ensure_ascii=False,indent=2))
    elif args.command=='matrix-compare':
        from .matrix_report import compare_matrices
        result=compare_matrices(args.first,args.second,args.output)
        print(json.dumps({k:v for k,v in result.items() if k in ('identical_missions','mission_count','first_counts','second_counts')},ensure_ascii=False,indent=2))
    elif args.command=='outcome-report':
        from .outcomes import report
        rows=report(args.source,args.output)
        print(json.dumps(dict(cases=len(rows),output=args.output)))
    elif args.command=='diagnose-step':
        from .diagnostics import diagnose_step
        result=diagnose_step(args.case,args.phase,args.output,budget_scale=args.budget_scale,native_prefix=args.native_prefix)
        return 1 if result['status']=='program_error' else 0
    elif args.command=='parameter-matrix':
        from .parameter_study import build_matrix
        from .data import write_json
        rows=build_matrix(args.design);write_json(args.output,rows)
        print(json.dumps(dict(cases=len(rows),output=args.output)))
    elif args.command=='parameter-report':
        from .parameter_study import report_study
        result=report_study(args.design,args.source,args.output)
        print(json.dumps({k:v for k,v in result.items() if k in ('cases','completed','configuration_errors','by_variant')},indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
