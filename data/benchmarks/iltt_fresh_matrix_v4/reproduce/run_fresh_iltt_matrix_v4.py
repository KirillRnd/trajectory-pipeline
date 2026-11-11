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

root=Path('runs/iltt_fresh_matrix_v4_full');root.mkdir(exist_ok=False)
(root/'inputs').mkdir();(root/'logs').mkdir()
design=Path('configs/search_graph_fresh_iltt_v4.json')
history=[]
baseline=Path('data/benchmarks/search_matrix_v1')
raw=json.loads((baseline/'matrix.json').read_text())
for r in raw:
    r['tof_days']=None
    r['solver']['irt_entry']='date'
missions=[Mission(**dict(r,solver=dict(r['solver'],budget_s=45,departure_budget_s=60,pazov_budget_s=90,psi_budget_s=120))).validate() for r in raw]
write_json(root/'matrix.json',[m.to_dict() for m in missions])
write_json(root/'design.json',json.loads(design.read_text()))
write_json(root/'environment.json',runtime_environment())
write_json(root/'study.json',dict(history=history,workers=15,seed_design_sha256=sha256(design),
    ephemerides={p.parent.name:sha256(p) for p in Path('data/ephemerides').glob('*/metadata.json')},source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),case_wall_limit_s=5100,notes=[
        'Same design, histories and numerical budgets for all 15 original matrix cases.',
        'Fifteen separate search processes; KIAM is not called from coordinator threads.',
        'No historical references: every chain starts from its date and angular branch.',
        'No adjustment or rerun of individual outcomes during this first pass.']))
for mission in missions:write_json(root/'inputs'/f'{mission.case_id}.json',mission.to_dict())

def execute(mission):
    name=mission.case_id;started=time.perf_counter();print(name+': started',flush=True)
    command=[sys.executable,'-m','trajectory_pipeline','search',str(root/'inputs'/f'{name}.json'),
             '--design',str(design),'--output',str(root/name)]
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
with ThreadPoolExecutor(max_workers=15) as executor:
    futures={executor.submit(execute,m):m.case_id for m in missions}
    for future in as_completed(futures):
        name=futures[future]
        try:rows[name]=future.result()
        except Exception as exc:rows[name]=dict(case_id=name,search_status='controller_failed',error=repr(exc))
        write_json(root/'results.json',[rows[m.case_id] for m in missions if m.case_id in rows])
print('All 15 searches returned',flush=True)
