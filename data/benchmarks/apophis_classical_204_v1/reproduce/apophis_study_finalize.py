import json,os
from pathlib import Path
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.search_graph import check_result
from trajectory_pipeline.runtime import runtime_environment
root=Path('runs/apophis_classical_204')
standard=Trajectory.load(root/'standard_solve/final')
check,kiam=check_result(standard,Mission(**standard.metadata['mission']))
write_json(root/'standard_independent_audit.json',dict(verification=check,kiam=kiam))
result=Trajectory.load(root/'chain_july_final/05_free_time')
summary=dict(launch_tdb=result.metadata['mission']['launch_tdb'],duration_days=result.metadata['mission']['tof_days'],
    verification=result.metadata['verification'],dm_limit=float(.999*np.sin(.642)),
    active_hours=float(result.metadata['verification']['fuel_kg']*11767.98/.036/3600),
    xenon_remaining_kg=float(64-result.metadata['verification']['fuel_kg']),
    iltt=result.metadata['mission']['solver']['iltt_resolved'],
    scopes=['central heliocentric segment','constant nominal F/c','rendezvous velocity boundary','no parking-orbit departure or capture'],
    engine_source='https://keldysh.ru/smallsat/news/2024/2412/suslov.pdf',
    engine_assumption='Two engines operating simultaneously at 18 mN each, Isp 1200 s; c=1200*9.80665 m/s; no variable solar-power model',
    spacecraft_assumption='204 kg at heliocentric departure, including 64 kg xenon; external initial impulse is not xenon consumption',
    runtime=runtime_environment(),docker_image_id=os.environ['TRAJECTORY_IMAGE_ID'],
    source_sha256={str(p):sha256(p) for p in [Path('trajectory_pipeline/iltt_entry.py'),Path('ILTT/ILTTToolbox.py'),Path('tests/test_iltt_date_entry.py')]})
write_json(root/'study_summary.json',summary)
print(json.dumps({k:summary[k] for k in ['duration_days','dm_limit','active_hours','xenon_remaining_kg','docker_image_id']},indent=2))
