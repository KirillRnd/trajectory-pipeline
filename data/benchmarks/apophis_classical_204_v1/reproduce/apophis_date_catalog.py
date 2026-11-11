import json
from pathlib import Path
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches
from trajectory_pipeline.data import write_json,DAY_S
import numpy as np
raw=next(x for x in json.loads(Path('configs/search_matrix_date_v4.json').read_text()) if x['target']=='Apophis')
rows=[]
for year in range(2027,2034):
 for month in range(1,13):
    raw['launch_tdb']=f'{year}-{month:02d}-01T00:00:00';m=Mission(**raw).validate()
    tb,eph,scale,initial,el,phase,branches=angular_branches(m)
    lam=branches[0]['lambda_initial']
    F,x0=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],lam,float(el[0]),0,1,float(el[2]),float(el[3]),float(el[1]),float(el[8]))
    rows.append(dict(date=raw['launch_tdb'],lambda_initial=lam,initial_duration_days=float(2*np.pi*tb.T_a(lam,float(el[0]))*scale.time_s/DAY_S),x0=x0.tolist()))
write_json('runs/apophis_classical_204/date_catalog.json',rows)
print(json.dumps([r for r in rows if .1<r['lambda_initial']<2.5],indent=2))
