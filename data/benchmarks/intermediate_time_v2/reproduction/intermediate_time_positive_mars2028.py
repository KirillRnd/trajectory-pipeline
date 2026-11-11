from pathlib import Path
import json
from trajectory_pipeline.data import write_json,sha256
from trajectory_pipeline.search_graph import worker,read
root=Path('runs/intermediate_time_positive_mars2028');root.mkdir(exist_ok=False)
p=Path('data/benchmarks/search_matrix_v1/earth_mars_2028');g=read(p/'graph.json')
node=next(k for k,n in g['nodes'].items() if n['request']['operation']=='cold' and n['status']=='completed')
cp=p/'nodes'/node/'run/stage_psi/mass';source=cp/read(cp/'continuation.json')['last_point']
for op in ('intermediate_release','physical_continue'):
    folder=root/op;folder.mkdir()
    request=dict(operation=op,mission=read(source/'trajectory.json')['mission'],parent_artifact=str(source),
                 parent_sha256=sha256(source/'trajectory.npz'),parent_metadata_sha256=sha256(source/'trajectory.json'),
                 bounds_days=[250,750],budget_s=120 if op=='intermediate_release' else 240)
    write_json(folder/'request.json',request);worker(folder/'request.json');result=read(folder/'result.json')
    print(op,result['status'],result.get('phase'),result.get('error','')[:400],flush=True)
    if result['status'] not in ('intermediate','completed'):break
    source=Path(result['artifact'])
