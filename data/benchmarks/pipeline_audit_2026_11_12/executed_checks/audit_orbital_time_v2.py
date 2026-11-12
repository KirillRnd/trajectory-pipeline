from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor,as_completed
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.composed_time import run_composed_time
from trajectory_pipeline.data import write_json

def work(path):
 source=Path(path);m=Mission.load(source/'mission.json')
 m=replace(m,time_policy={'bounds_days':[m.tof_days-1,m.tof_days+1]},solver=dict(m.solver,orbital_seed_path=str((source/'outer').resolve()),orbital_time_budget_s=480,orbital_time_trial_s=180,orbital_time_iterations=1))
 folder=Path('runs/audit_orbital_time_v2')/source.name
 result,state=run_composed_time(m,folder)
 print(source.name,state['status'],state.get('selected'),flush=True);return state
if __name__=='__main__':
 paths=list(Path('data/benchmarks/orbital_modes_v1/dry60').glob('mars_*'))
 with ProcessPoolExecutor(max_workers=4) as pool:rows=list(pool.map(work,paths))
 write_json(Path('runs/audit_orbital_time_v2/results.json'),rows)
