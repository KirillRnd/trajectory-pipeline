from pathlib import Path
from datetime import datetime,timedelta
import json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches,resolve_date_mission
from trajectory_pipeline.ephemerides import Ephemerides
from trajectory_pipeline.data import write_json,sha256

root=Path('runs/iltt_preflight_v4');root.mkdir(exist_ok=True)
base=json.loads(Path('data/benchmarks/search_matrix_v1/matrix.json').read_text())
design=json.loads(Path('configs/search_graph_fresh_iltt_v4.json').read_text());eph=Ephemerides();rows=[]
for original in base:
    for offset in design['date_offsets_days']:
        for branch in design['angular_branches']:
            raw=dict(original,tof_days=None,launch_tdb=(datetime.fromisoformat(original['launch_tdb'])+timedelta(days=offset)).isoformat(),solver=dict(original['solver'],irt_entry='date',iltt_branch=branch))
            row=dict(case_id=raw['case_id'],offset_days=offset,branch=branch)
            try:
                m=Mission(**raw).validate()
                tb,_,scale,_,el,phase,branches=angular_branches(m,eph)
                row.update(phase_rad=phase,branches=branches)
                m=resolve_date_mission(m,eph);row.update(status='resolved',iltt=m.solver['iltt_resolved'])
                row['time_interval_covered']=all(m.launch_jd>=eph.coverage(b)['start_jd'] and m.launch_jd+m.tof_days*1.5<=eph.coverage(b)['stop_jd'] for b in (m.departure,m.target))
            except Exception as exc:row.update(status='failed',error=type(exc).__name__+': '+str(exc))
            rows.append(row);write_json(root/'results.json',rows)
    print(original['case_id'],sum(r['status']=='resolved' for r in rows if r['case_id']==original['case_id']),'resolved branches',flush=True)
write_json(root/'coverage.json',{b:eph.coverage(b) for b in sorted({r[k] for r in base for k in ('departure','target')})})
