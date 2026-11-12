import json
from pathlib import Path
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.orbit_transition import reconcile_irt
root=Path('runs/coordinate_matrix_apophis_full_v1');root.mkdir(exist_ok=False);rows=[]
for row in json.loads(Path('runs/coordinate_matrix_v1/results.json').read_text()):
    if row['target']!='Apophis':continue
    source=Trajectory.load(Path('runs/coordinate_matrix_v1')/row['case_id']/row['last_result'])
    result,summary=reconcile_irt(source,{'earth':{'kind':'ephemerides'},'apophis':{'kind':'ephemerides'}},root/row['case_id'],coordinates=['iltt','costates'])
    rows.append(dict(case_id=row['case_id'],summary=summary));write_json(root/'results.json',rows)
    print(row['case_id'],summary['status'],flush=True)
