import sys,json,time
from pathlib import Path
from dataclasses import replace
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.verification import verify_irt
from trajectory_pipeline.bounded import verify_bounded
from trajectory_pipeline.contract import audit_configuration
from trajectory_pipeline.search_graph import check_result
from trajectory_pipeline.free_time import release_duration,audit_time_result

root=Path(sys.argv[1]);report=[];initial=json.loads((root/'request.json').read_text())
for stage in ['01_irt','02_departure','03_pazov','04_psi']:
    summary=json.loads((root/stage/'summary.json').read_text()) if (root/stage/'summary.json').exists() else json.loads((root/stage/'continuation.json').read_text())
    path=root/stage/(summary.get('last_result') or summary['last_point'])
    result=Trajectory.load(path);m=Mission(**result.metadata['mission'])
    for key in ['departure','target','launch_tdb','mass_kg','spacecraft','departure_mode','vinf_max_m_s']:
        assert m.to_dict()[key]==initial[key],key
    audit=audit_configuration(result,require_final=stage=='04_psi')
    verification=verify_irt(result) if stage in ['01_irt','02_departure'] else verify_bounded(result)
    assert verification['passed'],verification
    report.append(dict(stage=stage,artifact=str(path),parameter_audit=audit,verification=verification,departure=result.metadata.get('departure'),duration_days=m.tof_days,functional=result.metadata.get('functional_dimensionless')))
check,kiam=check_result(result,m);report[-1]['kiam']=kiam
assert check['fuel_kg']<=64
write_json(root/'independent_chain_audit.json',report)
print('PHYSICAL',m.launch_tdb,m.tof_days,check['fuel_kg'],kiam['passed'],flush=True)
bounds=[m.tof_days*.5,m.tof_days*1.5]
release=dict(status='running',parent_artifact=str(path),bounds_days=bounds)
write_json(root/'free_time.json',release)
try:
    freed=release_duration(result,result,bounds,time.perf_counter()+120)
    audit_time_result(freed,replace(m,time_policy=dict(bounds_days=bounds)))
    check,kiam=check_result(freed,Mission(**freed.metadata['mission']))
    freed.metadata['kiam_verification']=kiam;freed.save(root/'05_free_time')
    release.update(status='completed',artifact=str(root/'05_free_time'),verification=check,kiam=kiam,duration_days=freed.metadata['mission']['tof_days'],fuel_delta_kg=check['fuel_kg']-report[-1]['verification']['fuel_kg'])
except Exception as exc:release.update(status='failed',error=type(exc).__name__+': '+str(exc))
write_json(root/'free_time.json',release);print('TIME',release.get('duration_days'),release.get('verification',{}).get('fuel_kg'),release.get('error'),flush=True)
