from pathlib import Path
from time import perf_counter
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.search_graph import read,check_result
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.bounded import collocate
from trajectory_pipeline.intermediate_time import continue_physical_model
from trajectory_pipeline.problem import Mission
root=Path('runs/intermediate_time_joint_control');root.mkdir(exist_ok=False)
request=read(Path('runs/intermediate_time_positive_mars2028/intermediate_release/request.json'))
source=Trajectory.load(request['parent_artifact']);model=BoundedModel(**source.metadata['bounded_model'])
bridge=replace(model,a_max=1.2*model.a_max,q=1.2*model.q,beta=.7)
current=collocate(source,source,bridge,perf_counter()+20,'psi_mass');current.save(root/'bridge')
write_json(root/'request.json',dict(source=request['parent_artifact'],source_model=source.metadata['bounded_model'],bridge_model=current.metadata['bounded_model'],purpose='Real Mars regression exercising simultaneous beta and force change, unchanged mission hardware'))
result,status=continue_physical_model(current,root/'continuation');result.save(root/'last');write_json(root/'summary.json',status)
if status['status']=='completed':
    check,kiam=check_result(result,Mission(**result.metadata['mission']));write_json(root/'verification.json',dict(verification=check,kiam_verification=kiam))
print(status,flush=True)
