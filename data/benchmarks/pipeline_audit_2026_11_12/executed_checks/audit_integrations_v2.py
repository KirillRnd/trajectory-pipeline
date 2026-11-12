from pathlib import Path
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import worker
from trajectory_pipeline.runner import run_pipeline
from trajectory_pipeline.ummp import run_ummp,verify_ummp
import sys
kind=sys.argv[1];root=Path('runs/audit_integrations_v2')/kind
if kind=='source':
    m=Mission.load('runs/skill_repair_source_request.json')
    m=replace(m,solver=dict(m.solver,departure_budget_s=60,limit_budget_s=90,pazov_budget_s=90,psi_budget_s=180,bounded_attempt_s=25))
    result,state=run_pipeline(m,root)
    print(state,flush=True)
elif kind=='historical':
    s=Trajectory.load('data/benchmarks/ummp_apophis_156kg_benchmark/psi/fuel/point_0004')
    t,state=run_ummp(s,root)
    print(state,flush=True)
    if state['status']=='completed_stage':write_json(root/'replay.json',verify_ummp(t))
else:
    source=Path('data/benchmarks/accepted42_psi_v1/earth_apophis_2029_d+0/physical')
    if not source.exists():source=next(Path('data/benchmarks/accepted42_psi_v1').glob('*apophis*/physical'))
    t=Trajectory.load(source);root.mkdir(parents=True)
    request=dict(operation='ummp',mission=t.metadata['mission'],budget_s=300,parent_artifact=str(source),parent_sha256=sha256(source/'trajectory.npz'),parent_metadata_sha256=sha256(source/'trajectory.json'))
    write_json(root/'request.json',request);worker(root/'request.json');print((root/'result.json').read_text(),flush=True)