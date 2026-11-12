import json,sys,time,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission
ROOT=Path('runs/apophis_daily_routes_v1')
def solve(folder):
    from trajectory_pipeline.free_time import release_duration
    from trajectory_pipeline.contract import audit_configuration
    from trajectory_pipeline.kiam_verification import verify_kiam_psi
    summary=json.loads((folder/'summary.json').read_text());request=json.loads((folder/'request.json').read_text())
    out=folder/'free_time_recheck';out.mkdir(exist_ok=False)
    write_json(out/'request.json',dict(parent=summary['physical']['path'],bounds_days=request['bounds_days'],budget_s=120,source_sha256={p:sha256(p) for p in ['trajectory_pipeline/free_time.py','trajectory_pipeline/bangbang.py']}))
    source=Trajectory.load(summary['physical']['path']);row=dict(status='partial')
    try:
        result=release_duration(source,source,request['bounds_days'],time.perf_counter()+120)
        expected=replace(Mission(**request['mission']),tof_days=result.metadata['mission']['tof_days'])
        audit_configuration(result,expected,require_final=True);kiam=verify_kiam_psi(result);assert kiam['passed']
        result.metadata['kiam_verification']=kiam;result.save(out/'final')
        row.update(status='accepted',path=str(out/'final'),tof_days=expected.tof_days,fuel_kg=float(result.arrays['mass_kg'][0]-result.arrays['mass_kg'][-1]))
    except Exception as exc:row['error']=f'{type(exc).__name__}: {exc}'
    write_json(out/'summary.json',row)
def worker(folder):
    with (folder/'free_time_recheck.log').open('w') as log:
        try:subprocess.run([sys.executable,__file__,'one',str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=135)
        except subprocess.TimeoutExpired:write_json(folder/'free_time_recheck/summary.json',dict(status='partial',error='Hard free-time recheck timeout 135 s'))
    check=json.loads((folder/'free_time_recheck/summary.json').read_text())
    summary=json.loads((folder/'summary.json').read_text());write_json(folder/'pre_grid_fix_summary.json',summary)
    summary['stages'].append(dict(check,route_stage='free_time_after_grid_fix'))
    if check['status']=='accepted':summary.update(status='completed',phase='free_time',free_time=check)
    write_json(folder/'summary.json',summary)
    print(folder.name,check['status'],check.get('fuel_kg'),check.get('error'),flush=True)
    return dict(date=folder.name,**check)
if __name__=='__main__':
    if len(sys.argv)>1:solve(Path(sys.argv[2]))
    else:
        folders=[p for p in sorted((ROOT/'chains').iterdir()) if json.loads((p/'summary.json').read_text())['status']=='physical_fixed_time']
        write_json(ROOT/'free_time_recheck_design.json',dict(cases=[p.name for p in folders],workers=4,budget_s=120,reason='Fix uncovered final sample after duration rescaling; retain all accepted parents and previous attempts'))
        rows=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(worker,p) for p in folders]
            for future in as_completed(futures):rows.append(future.result());write_json(ROOT/'free_time_recheck_results.json',rows)
