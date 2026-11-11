"""Declared experiment runner: independent CLI searches, unchanged shared design."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import write_json, sha256
from trajectory_pipeline.runtime import runtime_environment

root=Path('runs/search_intermediate_matrix_v2');root.mkdir(exist_ok=False)
(root/'inputs').mkdir();(root/'logs').mkdir()
design=Path('configs/search_graph_intermediate_v2.json')
history=['data/benchmarks/free_time_physical_matrix_v1','data/benchmarks/psi',
         'data/benchmarks/search_graph_v1/bennu','data/benchmarks/search_graph_v1/ceres']
baseline=Path('data/benchmarks/search_matrix_v1')
failed={r['case_id'] for r in json.loads((baseline/'verified_results.json').read_text()) if not r['accepted']}
assert len(failed)==5
raw=[r for r in json.loads((baseline/'matrix.json').read_text()) if r['case_id'] in failed]
missions=[Mission(**dict(r,solver=dict(r['solver'],budget_s=30,departure_budget_s=40,pazov_budget_s=60,psi_budget_s=60))).validate() for r in raw]
write_json(root/'matrix.json',[m.to_dict() for m in missions])
write_json(root/'design.json',json.loads(design.read_text()))
write_json(root/'environment.json',runtime_environment())
write_json(root/'study.json',dict(history=history,workers=5,seed_design_sha256=sha256(design),
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),case_wall_limit_s=5100,notes=[
        'Same design, histories and numerical budgets for all five previously unsuccessful cases.',
        'Five separate search processes; KIAM is not called from coordinator threads.',
        'Historical solutions may be reused; report separates reuse from new calculation.',
        'No adjustment or rerun of individual outcomes during this first pass.']))
for mission in missions:write_json(root/'inputs'/f'{mission.case_id}.json',mission.to_dict())

def execute(mission):
    name=mission.case_id;started=time.perf_counter();print(name+': started',flush=True)
    command=[sys.executable,'-m','trajectory_pipeline','search',str(root/'inputs'/f'{name}.json'),
             '--design',str(design),'--history',*history,'--output',str(root/name)]
    error=None
    with (root/'logs'/f'{name}.log').open('w') as stream:
        process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:code=process.wait(timeout=5100)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            code=process.returncode;error='Search process group exceeded 5100 s'
    path=root/name/'summary.json';summary=json.loads(path.read_text()) if path.exists() else {}
    row=dict(case_id=name,exit_code=code,elapsed_s=time.perf_counter()-started,
             search_status=summary.get('status','controller_failed'),accepted=summary.get('accepted',0),
             original_conditions_found=summary.get('original_conditions_found',False),error=error)
    print(f'{name}: {row["search_status"]}; accepted nodes {row["accepted"]}; {row["elapsed_s"]:.1f} s',flush=True)
    return row

rows={}
with ThreadPoolExecutor(max_workers=5) as executor:
    futures={executor.submit(execute,m):m.case_id for m in missions}
    for future in as_completed(futures):
        name=futures[future]
        try:rows[name]=future.result()
        except Exception as exc:rows[name]=dict(case_id=name,search_status='controller_failed',error=repr(exc))
        write_json(root/'results.json',[rows[m.case_id] for m in missions if m.case_id in rows])
print('All five searches returned',flush=True)
