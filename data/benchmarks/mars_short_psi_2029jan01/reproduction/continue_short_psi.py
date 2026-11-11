from pathlib import Path
import json,subprocess,sys
from trajectory_pipeline.data import Trajectory,write_json,sha256
root=Path('runs/mars_short_psi_recovery_v1');root.mkdir(exist_ok=False)
base=Path('runs/mars_short_psi_v1');summary=json.loads((base/'stage_psi/summary.json').read_text());source=base/'stage_psi'/summary['last_result']
initial=Trajectory.load(source);anchor=initial.metadata['mission']['solver']['iltt_resolved']['tof_days'];steps=[]
for i in range(2):
 for op in ('intermediate_release','physical_continue'):
  tr=Trajectory.load(source);folder=root/f'{i+1}_{op}';folder.mkdir()
  request=dict(operation=op,mission=tr.metadata['mission'],budget_s=120 if op=='intermediate_release' else 300,
    parent_artifact=str(source),parent_sha256=sha256(source/'trajectory.npz'),parent_metadata_sha256=sha256(source/'trajectory.json'),bounds_days=[.5*anchor,1.5*anchor])
  write_json(folder/'request.json',request)
  with (folder/'worker.log').open('w') as log:
   subprocess.run([sys.executable,'-m','trajectory_pipeline','_search-worker',str(folder/'request.json')],stdout=log,stderr=subprocess.STDOUT,timeout=request['budget_s']+20)
  result=json.loads((folder/'result.json').read_text());steps.append(dict(folder=str(folder),**result));write_json(root/'steps.json',steps)
  print(i+1,op,result['status'],result.get('phase'),result.get('error'),flush=True)
  if not result.get('artifact'):sys.exit(1)
  source=Path(result['artifact'])
  if result['status']=='completed':
   write_json(root/'summary.json',dict(status='completed',final=str(source)));sys.exit(0)
write_json(root/'summary.json',dict(status='partial',last_result=str(source)))
