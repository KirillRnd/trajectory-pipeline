from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.search_graph import worker

def work(operation):
    source=Path('data/benchmarks/ummp_apophis_156kg_benchmark/psi/fuel/point_0004') if operation=='ummp' else Path('data/benchmarks/orbital_modes_v1/dry60/mars_impulse_impulse_dry60/outer')
    t=Trajectory.load(source);m=t.metadata['mission'];folder=Path('runs/audit_graph_terminals')/operation;folder.mkdir(parents=True)
    request=dict(operation=operation,mission=m,budget_s=300,parent_artifact=str(source),parent_sha256=sha256(source/'trajectory.npz'),parent_metadata_sha256=sha256(source/'trajectory.json'))
    if operation=='orbital':
        import json
        root=json.loads((source.parent/'mission.json').read_text())
        request['orbital_maneuvers']=root['orbital_maneuvers']
    write_json(folder/'request.json',request);worker(folder/'request.json')
    print(operation,(folder/'result.json').read_text(),flush=True)
if __name__=='__main__':
    with ProcessPoolExecutor(max_workers=2) as pool:list(pool.map(work,['ummp','orbital']))