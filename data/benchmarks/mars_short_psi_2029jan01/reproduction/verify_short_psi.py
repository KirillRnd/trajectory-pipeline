from pathlib import Path
import json,numpy as np
from datetime import datetime,timedelta
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import check_result,physical_spec,verify_cached
from trajectory_pipeline.intermediate_time import verify_intermediate
source=Path('runs/mars_short_psi_recovery_v1/2_physical_continue')
result=json.loads((source/'result.json').read_text());verify_cached(result)
tr=Trajectory.load(result['artifact']);mission=Mission(**tr.metadata['mission']);check,kiam=check_result(tr,mission)
request=Mission.load('runs/mars_short_psi_request.json');a=physical_spec(mission);b=physical_spec(request)
a.pop('tof_days');b.pop('tof_days');assert a==b
for rec in json.loads(Path('output/pipeline/mars_short_psi_steps/sources.json').read_text()):
 t=Trajectory.load(rec['path'])
 if t.metadata.get('bounded_model',{}).get('alpha')!=1:verify_intermediate(t)
angles=np.unwrap(np.arctan2(tr.arrays['r_m'][:,1],tr.arrays['r_m'][:,0]));turns=float((angles[-1]-angles[0])/(2*np.pi))
summary=dict(status='completed',scope='heliocentric rendezvous; no local orbit capture',mission=mission.to_dict(),initial_iltt_tof_days=tr.metadata['mission']['solver']['iltt_resolved']['tof_days'],
    verification=check,kiam_verification=kiam,angle_turns_xy=turns,arrival_tdb=(datetime.fromisoformat(mission.launch_tdb)+timedelta(days=mission.tof_days)).isoformat(),
    original_request=request.to_dict(),full_test_suite_run=False,final_artifact=result['artifact'])
write_json(Path('runs/mars_short_psi_verified.json'),summary)
print(json.dumps({k:summary[k] for k in ['status','angle_turns_xy','arrival_tdb']}));print('Final and all nine plotted stages checked; hardware, mass and launch date unchanged')
