import json
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.date_sweep import _reference_mission,_identity,_fast_attempt
root=Path('runs/apophis_daily_routes_v1');target=root/'chains/2028-02-23'
request=json.loads((target/'request.json').read_text());wanted=Mission(**request['mission'])
anchors=json.loads((root/'design.json').read_text())['anchors']
sources=[root/'chains'/r['launch_tdb'][:10]/'physical' for r in anchors]
source=min(sources,key=lambda p:abs(_reference_mission(Trajectory.load(p)).launch_jd-wanted.launch_jd))
base=_reference_mission(Trajectory.load(source))
def attempt(free):
    out=target/('r_free' if free else 'r_fixed');out.mkdir(exist_ok=False)
    policy=dict(bounds_days=request['bounds_days']) if free else None
    mission=replace(base,case_id=wanted.case_id,launch_tdb=wanted.launch_tdb,time_policy=policy)
    plan=dict(reference=str(source.resolve()),reference_sha256=_identity(source),fast_budget_s=120,time_policy=policy,selection='Nearest date among original seven accepted physical anchors')
    write_json(out/'sweep.json',plan);write_json(out/'mission.json',mission.to_dict())
    result=_fast_attempt(out,mission,out/'mission.json',120);print('R',free,result,flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(attempt,[False,True]))
