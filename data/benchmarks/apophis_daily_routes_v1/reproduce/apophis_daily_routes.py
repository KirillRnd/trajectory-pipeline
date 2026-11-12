"""Declared daily windows and ordinary module chains, no cross-date transfer."""
import json,sys,time,subprocess,traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission

ROOT=Path('runs/apophis_daily_routes_v1')

def chain(source,folder):
    from trajectory_pipeline.departure import run_departure
    from trajectory_pipeline.pazov import run_pazov
    from trajectory_pipeline.psi import run_psi
    from trajectory_pipeline.verification import verify_irt
    from trajectory_pipeline.bounded import verify_bounded
    from trajectory_pipeline.contract import audit_configuration,make_request,specification
    from trajectory_pipeline.kiam_verification import verify_kiam_psi
    from trajectory_pipeline.free_time import release_duration
    from trajectory_pipeline.intermediate_time import release_intermediate_duration,continue_physical_model,verify_intermediate
    folder.mkdir(parents=True,exist_ok=True)
    current=Trajectory.load(source);assert verify_irt(current)['passed']
    base=Mission.load('configs/apophis_spd50m_204.json')
    original=Mission(**current.metadata['mission'])
    assert abs(original.solver.get('iltt_dm_limit',.5981996389807971)-.5981996389807971)<1e-12
    assert original.mass_kg==204 and original.spacecraft==base.spacecraft
    solver=dict(original.solver);solver.update({k:v for k,v in base.solver.items() if 'budget' in k or k=='bounded_attempt_s'})
    mission=replace(original,solver=solver)
    current.metadata['mission']=mission.to_dict()
    bounds=[.5*mission.tof_days,min(1.5*mission.tof_days,1095.75)]
    write_json(folder/'request.json',dict(source=str(source),source_sha256=sha256(Path(source)/'trajectory.npz'),mission=mission.to_dict(),bounds_days=bounds,dm_policy='original empirical bound only'))
    if not (folder/'00_irt').exists():current.save(folder/'00_irt')
    else:
        saved=Trajectory.load(folder/'00_irt')
        assert saved.metadata['mission']==current.metadata['mission']
        current=saved
    request=make_request(mission)
    result=dict(date=mission.launch_tdb,status='running',phase='departure',stages=[],physical=None,free_time=None)
    def record(phase,status):
        result['phase']=phase;result['stages'].append(dict(status,route_stage=phase));write_json(folder/'summary.json',result)
    try:
        dep_checkpoint=folder/'01_departure/continuation.json'
        saved_dep=json.loads(dep_checkpoint.read_text()) if dep_checkpoint.exists() else {}
        if saved_dep.get('status')=='completed_stage':
            status=saved_dep;current=Trajectory.load(folder/'01_departure'/status['last_point'])
        else:current,status=run_departure(current,folder/'01_departure',resume=(folder/'01_departure').exists())
        current=Trajectory.load(folder/'01_departure'/status['last_point'])
        record('departure',status)
        audit_configuration(current,mission,request)
        if status['status']=='completed_stage':
            saved_path=folder/'02_pazov/summary.json'
            saved_pazov=json.loads(saved_path.read_text()) if saved_path.exists() else {}
            if saved_pazov.get('status')=='completed_stage':
                status=saved_pazov;current=Trajectory.load(folder/'02_pazov'/status['last_result'])
            else:current,status=run_pazov(current,folder/'02_pazov',target_alpha=.5,resume=(folder/'02_pazov').exists())
            current=Trajectory.load(folder/'02_pazov'/status['last_result'])
            record('pazov',status)
            audit_configuration(current,mission,request)
            current,status=run_psi(current,folder/'03_psi',resume=(folder/'03_psi').exists())
            current=Trajectory.load(folder/'03_psi'/status['last_result']);record('psi',status)
        complete=status['status'] in ('completed','completed_stage') and current.metadata.get('stage')=='psi'
        if not complete:
            for cycle in range(2):
                verify_intermediate(current)
                try:
                    current=release_intermediate_duration(current,bounds,time.perf_counter()+120,folder/f'release_{cycle}')
                    record('intermediate_time',dict(status='completed',tof_days=current.metadata['mission']['tof_days']))
                except (ValueError,RuntimeError,TimeoutError) as exc:record('intermediate_time',dict(status='partial',error=str(exc)))
                current,status=continue_physical_model(current,folder/f'continue_{cycle}');record('continue_physical',status)
                if status['status']=='completed':complete=True;break
        if complete:
            actual=Mission(**current.metadata['mission'])
            audit_configuration(current,replace(mission,tof_days=actual.tof_days),require_final=True)
            check=verify_bounded(current);kiam=verify_kiam_psi(current)
            assert check['passed'] and kiam['passed']
            current.metadata.update(verification=check,kiam_verification=kiam);current.save(folder/'physical')
            result['physical']=dict(path=str(folder/'physical'),tof_days=actual.tof_days,fuel_kg=float(current.arrays['mass_kg'][0]-current.arrays['mass_kg'][-1]),verification=check,kiam=kiam)
            record('physical',dict(status='accepted'))
            try:
                final=release_duration(current,current,bounds,time.perf_counter()+120)
                actual=Mission(**final.metadata['mission']);audit_configuration(final,replace(mission,tof_days=actual.tof_days),require_final=True)
                kiam=verify_kiam_psi(final);assert kiam['passed'];final.metadata['kiam_verification']=kiam
                final.save(folder/'free_time')
                result['free_time']=dict(path=str(folder/'free_time'),tof_days=actual.tof_days,fuel_kg=float(final.arrays['mass_kg'][0]-final.arrays['mass_kg'][-1]))
                record('free_time',dict(status='accepted'))
            except (ValueError,RuntimeError,TimeoutError) as exc:record('free_time',dict(status='partial',error=str(exc)))
        result['status']='completed' if result['free_time'] else 'physical_fixed_time' if result['physical'] else 'partial'
    except Exception as exc:
        result.update(status='error',error=f'{type(exc).__name__}: {exc}');(folder/'error.log').write_text(traceback.format_exc())
    write_json(folder/'summary.json',result)

def worker(source):
    date=Trajectory.load(source).metadata['mission']['launch_tdb'][:10];folder=ROOT/'chains'/date
    with (ROOT/(date+'.log')).open('w') as log:
        try:
            subprocess.run([sys.executable,__file__,'chain',str(source),str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=2400)
        except subprocess.TimeoutExpired:
            write_json(folder/'hard_timeout.json',dict(timeout_s=2400))
    summary=json.loads((folder/'summary.json').read_text()) if (folder/'summary.json').exists() else dict(date=date,status='error',error='No summary')
    if (folder/'hard_timeout.json').exists():summary.update(status='timeout',error='Hard route budget 2400 s; preserved checkpoints')
    print('CHAIN',date,summary['status'],summary.get('phase'),flush=True)
    return summary

def main():
    from trajectory_pipeline.seed_sweep import run_seed_sweep
    ROOT.mkdir(exist_ok=False);(ROOT/'chains').mkdir()
    old=json.loads(Path('runs/apophis_early_sweep_2027_2033_v1/results.json').read_text())
    anchors=[r for r in old if r['status']=='accepted'];assert len(anchors)==7
    design=json.loads(Path('configs/apophis_early_sweep_2027_2033.json').read_text());design.update(step_days=1,workers=4)
    windows=[('2028-01-28','2028-03-10'),('2029-06-01','2029-06-29')]
    write_json(ROOT/'design.json',dict(windows=windows,step_days=1,anchors=anchors,hardware=Mission.load('configs/apophis_spd50m_204.json').to_dict(),dm_limit=.5981996389807971,route_workers=4,hard_route_budget_s=2400))
    futures=[];dates={r['launch_tdb'] for r in anchors}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures.extend(pool.submit(worker,r['artifact']) for r in anchors)
        for i,(start,stop) in enumerate(windows):
            d=dict(design,start_tdb=start+'T00:00:00',stop_tdb=stop+'T00:00:00')
            sweep=ROOT/f'daily_{i}';run_seed_sweep(Mission.load('configs/apophis_spd50m_204.json'),d,sweep)
            for r in json.loads((sweep/'results.json').read_text()):
                if r['status']=='accepted' and r['launch_tdb'] not in dates:
                    futures.append(pool.submit(worker,r['artifact']));dates.add(r['launch_tdb'])
        rows=[]
        for future in as_completed(futures):
            rows.append(future.result());write_json(ROOT/'routes.json',sorted(rows,key=lambda r:r['date']))
    write_json(ROOT/'finished.json',dict(routes=len(rows),statuses={s:sum(r['status']==s for r in rows) for s in set(r['status'] for r in rows)}))

if __name__=='__main__':
    if len(sys.argv)>1:chain(Path(sys.argv[2]),Path(sys.argv[3]))
    else:main()
