from pathlib import Path
from dataclasses import replace
import json
from trajectory_pipeline.data import Trajectory,write_json,sha256
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.accepted_irt_routes import physical,run_case
from trajectory_pipeline.orbital_pipeline import verify_orbital_mission
from trajectory_pipeline.runner import run_pipeline
rows=[]
for p in sorted(Path('data/benchmarks/accepted42_psi_v1').glob('*/physical')):
    try:
        t=Trajectory.load(p);c=physical(t);m=t.metadata['mission']
        rows.append(dict(case_id=m['case_id'],target=m['target'],launch=m['launch_tdb'],passed=True,fuel_kg=c['fuel_kg'],source=str(p),arrays_sha256=sha256(p/'trajectory.npz')))
    except Exception as e:rows.append(dict(source=str(p),passed=False,error=str(e)))
write_json(Path('runs/audit_replay_physical.json'),rows)
orb=[]
for p in sorted(Path('runs/audit_orbital_time_v2').glob('mars_*')):
    c=verify_orbital_mission(p);s=json.loads((p/'summary.json').read_text());trials=json.loads((p/'time_trials.json').read_text())
    orb.append(dict(case_id=p.name,passed=c['passed'],selected=s['selected'],accepted_trials=sum(t['accepted'] for t in trials),trials=len(trials)))
write_json(Path('runs/audit_replay_orbital.json'),orb)
m=Mission.load('runs/skill_repair_source_request.json');m=replace(m,solver=dict(m.solver,departure_budget_s=60,limit_budget_s=90,pazov_budget_s=90,psi_budget_s=180,bounded_attempt_s=25))
_,s=run_pipeline(m,'runs/audit_integrations_v2/source',resume=True)
cases=json.loads(Path('runs/audit_generic204/design.json').read_text())['cases'];r=run_case((cases[0],'runs/audit_generic204','primary'))
write_json(Path('runs/audit_resume.json'),dict(source=s['status'],controller=r['status']))
print(dict(physical_passed=sum(r['passed'] for r in rows),physical_total=len(rows),orbital_passed=sum(r['passed'] for r in orb),source_resume=s['status'],controller_resume=r['status']))