from pathlib import Path
from trajectory_pipeline.data import write_json
from trajectory_pipeline.accepted_irt_routes import design,run_case
root=Path('runs/audit_generic204');root.mkdir()
write_json(root/'sources.json',[dict(case_id='apophis204',source='runs/audit_integrations_v2/source/resolved_irt',settings=dict(departure_budget_s=60,limit_budget_s=90,pazov_budget_s=90,psi_budget_s=180,bounded_attempt_s=25),horizon_days=1095.75)])
cases=design(root,root/'sources.json')
print(run_case((cases[0],str(root),'primary')),flush=True)