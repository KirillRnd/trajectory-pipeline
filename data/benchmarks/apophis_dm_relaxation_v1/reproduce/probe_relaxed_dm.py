import json,subprocess,sys,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from trajectory_pipeline.data import write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.seed_sweep import collect_case

root=Path('runs/apophis_dm_relaxation_v1');root.mkdir(exist_ok=False)
old=Path('runs/apophis_early_sweep_2027_2033_v1')
audit=json.loads(Path('runs/iltt_failure_audit.json').read_text())
hits=[r for r in audit if r.get('dm_at_bound')]
chosen=[hits[i]['case_id'] for i in np.linspace(0,len(hits)-1,6,dtype=int)]+['date_0127_branch_00']
write_json(root/'design.json',dict(selection='Six evenly spaced indices from 61 chronologically ordered boundary hits, plus accepted 2029-06-08 control',cases=chosen,dm_limits=[.999*np.sin(.642),.8,1.0],workers=4,timeout_s=150))
jobs=[]
for case in chosen:
    raw=json.loads((old/'inputs'/(case+'.json')).read_text())
    for limit in [.999*np.sin(.642),.8,1.0]:
        m=json.loads(json.dumps(raw));m['solver']['iltt_dm_limit']=float(limit)
        folder=root/(case+f'_dm{limit:.4f}');inp=root/(folder.name+'.json');write_json(inp,m)
        jobs.append((m,folder,inp,limit))
def run(job):
    raw,folder,inp,limit=job
    error=None
    with (root/(folder.name+'.log')).open('w') as log:
        try:subprocess.run([sys.executable,'-m','trajectory_pipeline','solve-irt',str(inp),'--output',str(folder)],stdout=log,stderr=subprocess.STDOUT,timeout=150)
        except subprocess.TimeoutExpired:error='Hard worker time limit: 150 s'
    row=collect_case(folder,Mission(**raw),error);row['dm_limit']=float(limit)
    if (folder/'mission.json').exists():
        record=json.loads((folder/'mission.json').read_text())['solver']['iltt_resolved']
        row.update(dm_corrected=record['x_corrected'][0],iltt_residual=float(np.linalg.norm(record['orbit_phase_residual'])))
    else:
        match=re.search(r'residual=\[(.*?)\]; x=\[(.*?)\]',row.get('error') or '',re.S)
        if match:row.update(iltt_residual=float(np.linalg.norm(np.fromstring(match[1],sep=' '))),dm_corrected=float(np.fromstring(match[2],sep=' ')[0]))
    return row
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(run,jobs):
        rows.append(row);write_json(root/'results.json',rows)
        print(row['launch_tdb'],row['dm_limit'],row['status'],row.get('iltt_residual'),row.get('dm_corrected'),flush=True)
