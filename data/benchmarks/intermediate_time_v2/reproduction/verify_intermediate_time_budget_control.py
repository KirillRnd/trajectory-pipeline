from pathlib import Path
import json
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import read,verify_cached,check_result,physical_spec,changes
from trajectory_pipeline.intermediate_time import verify_intermediate
root=Path('runs/intermediate_time_budget_control');rows=[]
for base in read(root/'matrix.json'):
    case=base['case_id'];folder=root/case
    result=read(folder/'result.json');selection=read(folder/'selection.json');request=read(folder/'request.json')
    parent=Trajectory.load(folder/'parent');verify_intermediate(parent)
    before=Trajectory.load(selection['selected']['artifact'])
    assert physical_spec(Mission(**parent.metadata['mission']))==physical_spec(Mission(**before.metadata['mission']))
    record=dict(case_id=case,status=result['status'],phase=result['phase'],selection=selection,request=request,error=result.get('error'))
    if result.get('artifact'):
        verify_cached(result);trajectory=Trajectory.load(result['artifact']);actual=Mission(**trajectory.metadata['mission'])
        assert physical_spec(actual)==physical_spec(Mission(**parent.metadata['mission']))
        if result['status']=='completed':
            check,kiam=check_result(trajectory,actual);record.update(verification=check,kiam_verification=kiam,fuel_kg=check['fuel_kg'])
        else:record['verification']=verify_intermediate(trajectory)
        record.update(mission=actual.to_dict(),model=trajectory.metadata['bounded_model'],changes=changes(Mission(**base),actual),artifact=result['artifact'])
    source_rows=read(Path('runs')/selection['selected']['series']/'verified_results.json')
    old=next(r for r in source_rows if r['case_id']==case)
    old_node=next(s for s in old['stops'] if s['node']==selection['selected']['node'])
    record['route']=old_node['route']+' → дополнительное продолжение с едиными увеличенными бюджетами'
    checkpoints=[]
    for cp in (folder/'continuation').rglob('continuation.json'):
        c=read(cp);checkpoints.append(dict(path=str(cp),stop_reason=c.get('stop_reason'),reached_parameter=c.get('reached_parameter'),last_point=c.get('last_point'),last_event=c.get('history',[None])[-1]))
    record['checkpoints']=checkpoints;rows.append(record)
    print(case,result['status'],result['phase'],'verified',flush=True)
write_json(root/'verified_results.json',rows)
write_json(root/'totals.json',dict(cases=len(rows),accepted=sum(r['status']=='completed' for r in rows),partial=sum(r['status']=='partial' for r in rows)))
print('Independent budget-control checks complete')
