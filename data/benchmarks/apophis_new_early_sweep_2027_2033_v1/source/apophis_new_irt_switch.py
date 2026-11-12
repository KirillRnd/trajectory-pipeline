import json,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from trajectory_pipeline.coordinate_matrix import worker
from trajectory_pipeline.data import write_json
ROOT=Path('runs/apophis_new_early_sweep_2027_2033_v1')
if __name__=='__main__':
 while True:
  p=ROOT/'summary.json'
  if p.exists() and json.loads(p.read_text()).get('status')=='finished':break
  time.sleep(5)
 results=json.loads((ROOT/'results.json').read_text());missions={m['case_id']:m for m in json.loads((ROOT/'missions.json').read_text())}
 tasks=[(missions[r['case_id']],str(ROOT/'coordinate_fallback'/r['case_id'])) for r in results if r['status']!='accepted']
 write_json(ROOT/'fallback_design.json',dict(rule='Same date-derived branch and duration horizon; unchanged R bound; ILTT then costates, separate 20 s budgets and 70 iterations',requests=tasks))
 rows=[]
 with ProcessPoolExecutor(max_workers=8) as pool:
  for f in as_completed([pool.submit(worker,t) for t in tasks]):
   r=f.result();rows.append(r);write_json(ROOT/'fallback_results.json',rows);print(len(rows),len(tasks),r['case_id'],r['accepted'],flush=True)
