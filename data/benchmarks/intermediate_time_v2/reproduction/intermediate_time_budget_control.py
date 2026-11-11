"""Uniform solver-budget control from verified intermediate graph checkpoints."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from time import perf_counter
import json,math,subprocess,sys
from trajectory_pipeline.data import Trajectory,Scales,sha256,write_json
from trajectory_pipeline.search_graph import read,verify_cached,physical_spec
from trajectory_pipeline.intermediate_time import verify_intermediate
from trajectory_pipeline.problem import Mission
root=Path('runs/intermediate_time_budget_control');root.mkdir(exist_ok=False)
bases=read(Path('runs/search_intermediate_matrix_v2/matrix.json'))
settings=dict(psi_budget_s=180,bounded_attempt_s=40,collocation_budget_s=12,shooting_budget_s=20)
write_json(root/'study.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    selection='min(abs(log(model_force/requested_force)) + (1-beta)), tie: source path; same rule for all five',
    settings=settings,workers=5,node_budget_s=400,hard_timeout_s=420,
    code={p.name:sha256(p) for p in Path('trajectory_pipeline').glob('*.py')},
    note='Only numerical budgets change; each selected parent physical specification is preserved exactly. One continuation per case.'))
write_json(root/'matrix.json',bases)
prepared=[]
for base in bases:
    case=base['case_id'];candidates=[]
    for series in ('search_intermediate_matrix_v2','search_intermediate_long_v2'):
        graph=read(Path('runs')/series/case/'graph.json')
        for nid,node in graph['nodes'].items():
            if node['request']['operation']!='physical_continue' or node['status']!='partial' or not node.get('artifact'):continue
            verify_cached(node);source=Trajectory.load(node['artifact']);model=source.metadata['bounded_model']
            scale=Scales(**source.metadata['scales']);mission=Mission(**source.metadata['mission'])
            ratio=model['a_max']*scale.acceleration_m_s2*mission.mass_kg/mission.spacecraft['thrust_N']
            candidates.append(dict(distance=abs(math.log(ratio))+(1-model['beta']),series=series,node=nid,
                artifact=node['artifact'],arrays_sha256=node['arrays_sha256'],metadata_sha256=node['metadata_sha256'],force_ratio=ratio,beta=model['beta']))
    candidates.sort(key=lambda x:(x['distance'],x['artifact']));selected=candidates[0]
    source=Trajectory.load(selected['artifact']);verify_intermediate(source)
    before=Mission(**source.metadata['mission']);after=Mission(**dict(before.to_dict(),solver=dict(before.solver,**settings))).validate()
    assert physical_spec(before)==physical_spec(after)
    source.metadata['mission']=after.to_dict();folder=root/case;folder.mkdir();source.save(folder/'parent')
    write_json(folder/'selection.json',dict(selected=selected,candidates=candidates,original_solver=before.solver,new_solver=after.solver))
    request=dict(operation='physical_continue',mission=after.to_dict(),budget_s=400,parent_artifact=str(folder/'parent'),
                 parent_sha256=sha256(folder/'parent/trajectory.npz'),parent_metadata_sha256=sha256(folder/'parent/trajectory.json'))
    write_json(folder/'request.json',request);prepared.append(case)
def execute(case):
    folder=root/case;started=perf_counter();print(case+': budget control started',flush=True)
    with (folder/'worker.log').open('w') as log:
        try:
            process=subprocess.run([sys.executable,'-m','trajectory_pipeline','_search-worker',str(folder/'request.json')],stdout=log,stderr=subprocess.STDOUT,timeout=420)
            result=read(folder/'result.json')
        except subprocess.TimeoutExpired:
            result=dict(status='failed',phase='physical_continue',error='Uniform budget-control timeout');write_json(folder/'result.json',result)
    row=dict(case_id=case,status=result['status'],phase=result['phase'],elapsed_s=perf_counter()-started)
    print(case+': '+result['status']+' / '+result['phase'],flush=True);return row
rows={}
with ThreadPoolExecutor(max_workers=5) as pool:
    for future in as_completed([pool.submit(execute,c) for c in prepared]):
        row=future.result();rows[row['case_id']]=row;write_json(root/'results.json',[rows[c] for c in prepared if c in rows])
print('All five uniform budget controls returned',flush=True)
