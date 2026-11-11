from pathlib import Path
import json
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.search_graph import verify_cached,physical_spec
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.intermediate_time import verify_intermediate
from trajectory_pipeline.verification import verify_irt
root=Path('runs/mars2029_date_graph_v3');g=json.loads((root/'graph.json').read_text());rows=[]
for key,n in g['nodes'].items():
    row=dict(node=key,operation=n['request']['operation'],status=n['status'],phase=n['phase'],error=n.get('error'),branch=n['request']['mission']['solver']['iltt_branch'])
    if n.get('artifact'):
        verify_cached(n);tr=Trajectory.load(n['artifact']);check=verify_intermediate(tr)
        actual=Mission(**tr.metadata['mission']);wanted=Mission(**n['request']['mission'])
        a,b=physical_spec(actual),physical_spec(wanted);a.pop('tof_days');b.pop('tof_days');assert a==b
        row.update(mission=actual.to_dict(),model=tr.metadata['bounded_model'],verification=check,artifact=n['artifact'])
    if n['request']['operation']=='cold':
        folder=root/'nodes'/key/'run';m=json.loads((folder/'mission.json').read_text());row['iltt_entry']=m['solver']['iltt_resolved']
        diag=folder/'stage_irt'/'diagnostics.json'
        if diag.exists():row['irt_diagnostics']=json.loads(diag.read_text())
        if (folder/'stage_irt'/'irt').exists():
            tr=Trajectory.load(folder/'stage_irt'/'irt');check=verify_irt(tr);assert check['passed'];row['irt_recheck']=check
        for f in folder.rglob('continuation.json'):
            cp=json.loads(f.read_text())
            row.setdefault('continuations',[]).append(dict(path=str(f),status=cp['status'],stop_reason=cp.get('stop_reason'),reached_parameter=cp.get('reached_parameter')))
    rows.append(row)
write_json(root/'verified_results.json',rows)
for r in rows:
    print(r['operation'],r['branch'],r['status'],r.get('verification',{}).get('fuel_kg'),r.get('iltt_entry',{}).get('tof_days'))
print('All declared artifacts independently checked; physical PSI not accepted')
