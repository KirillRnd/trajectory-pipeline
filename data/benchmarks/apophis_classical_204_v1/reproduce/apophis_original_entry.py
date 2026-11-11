import json,time
from pathlib import Path
from trajectory_pipeline.iltt_entry import resolve_date_mission,angular_branches
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import write_json,DAY_S
import numpy as np
raw=json.loads(Path('runs/apophis_classical_204/chain_july_final/request.json').read_text())
raw.update(case_id='apophis_original_date_204',launch_tdb='2029-02-14T12:00:00')
m=Mission(**raw);tb,eph,scale,initial,el,phase,branches=angular_branches(m)
record=dict(request=m.to_dict(),phase=phase,branch=branches[0],initial_duration_days=float(2*np.pi*tb.T_a(branches[0]['lambda_initial'],el[0])*scale.time_s/DAY_S))
start=time.perf_counter()
try:
    result=resolve_date_mission(m);record.update(status='resolved',result=result.to_dict())
except Exception as exc:record.update(status='failed',error=type(exc).__name__+': '+str(exc))
record['elapsed_s']=time.perf_counter()-start
write_json('runs/apophis_classical_204/original_date_recheck.json',record)
print(json.dumps(record,ensure_ascii=False),flush=True)
