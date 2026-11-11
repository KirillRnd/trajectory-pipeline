import json,sys,time
from pathlib import Path
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.runner import run_irt
from trajectory_pipeline.departure import run_departure
from trajectory_pipeline.pazov import run_pazov
from trajectory_pipeline.psi import run_psi

date=sys.argv[1] if len(sys.argv)>1 else '2029-07-01T00:00:00'
folder=Path(sys.argv[2]) if len(sys.argv)>2 else Path('runs/apophis_classical_204/chain_'+date[:10])
folder.mkdir(exist_ok=False)
raw=next(x for x in json.loads(Path('configs/search_matrix_date_v4.json').read_text()) if x['target']=='Apophis')
raw.update(case_id='apophis_204_'+date[:10],launch_tdb=date,mass_kg=204)
raw['spacecraft']=dict(thrust_N=.036,exhaust_velocity_m_s=1200*9.80665,dry_mass_kg=140)
raw['solver'].update(budget_s=180,attempt_budget_s=90,departure_budget_s=240,limit_budget_s=300,pazov_budget_s=300,psi_budget_s=600,bounded_attempt_s=45,iltt_budget_s=90)
m=Mission(**raw).validate();write_json(folder/'request.json',m.to_dict())
summary=run_irt(m,folder/'01_irt');write_json(folder/'progress.json',dict(stage='irt',summary=summary));print('IRT',summary['status'],flush=True)
if summary['status']!='completed_stage':sys.exit(2)
current=Trajectory.load(folder/'01_irt'/summary['last_result'])
for name,fn in [('02_departure',run_departure),('03_pazov',run_pazov),('04_psi',run_psi)]:
    current,status=fn(current,folder/name)
    write_json(folder/'progress.json',dict(stage=name,summary=status));print(name,status.get('status'),flush=True)
    if current is None or status.get('status') not in ('completed','completed_stage'):
        print(json.dumps(status,default=str),flush=True);sys.exit(2)
write_json(folder/'summary.json',dict(status='completed',last_result='04_psi/'+status.get('last_result','final')))
