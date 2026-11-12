import json,re,collections
from pathlib import Path
import numpy as np
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches,resolve_date_mission
import trajectory_pipeline.iltt_entry as entry
from trajectory_pipeline.data import write_json

root=Path('runs/apophis_early_sweep_2027_2033_v1')
rows=json.loads((root/'results.json').read_text());audit=[]
for row in rows:
    if row['status']=='accepted':continue
    err=row['error'];m=Mission.load(root/'inputs'/ (row['case_id']+'.json'))
    tb,eph,scale,initial,el,phase,branches=angular_branches(m)
    rec=dict(case_id=m.case_id,date=m.launch_tdb,error=err)
    match=re.search(r'; residual=\[(.*?)\]; x=\[(.*?)\]; x0=\[(.*?)\]',err,re.S)
    if match:
        residual,x,x0=[np.fromstring(t,sep=' ') for t in match.groups()]
        rec.update(residual_norm=float(np.linalg.norm(residual)),dm_at_bound=bool(abs(x[0])>.999*np.sin(.642)-1e-5),initial_saturated=bool(abs(x0[0])>=.999*np.sin(.642)),x=x.tolist())
        F,_=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],branches[0]['lambda_initial'],el[0],0,1,el[2],el[3],el[1],el[8])
        original=tb.solve_ivp
        def integration(*args,**kwargs):
            sol=original(*args,**kwargs)
            rec['integration']=dict(success=sol.success,message=sol.message,end=float(sol.t[-1]),requested=float(args[1][-1]))
            return sol
        tb.solve_ivp=integration
        try:F(x)
        except Exception as exc:rec['replay_error']=str(exc)
        finally:tb.solve_ivp=original
    else:
        original=entry.least_squares
        def logged(fun,*args,**kwargs):
            def wrapped(x):
                try:return fun(x)
                except Exception as exc:
                    rec['failed_trial']=dict(x=x.tolist(),duration_days=float(2*np.pi*tb.T_a(x[5],x[4])*scale.time_s/86400),error=str(exc));raise
            return original(wrapped,*args,**kwargs)
        entry.least_squares=logged
        try:resolve_date_mission(m)
        except Exception as exc:rec['reproduced_error']=str(exc)
        finally:entry.least_squares=original
    audit.append(rec)
write_json('runs/iltt_failure_audit.json',audit)
print('failures',len(audit),'at_dm_bound',sum(r.get('dm_at_bound',False) for r in audit),'initial_saturated',sum(r.get('initial_saturated',False) for r in audit))
print('integration',collections.Counter(r.get('integration',{}).get('success') for r in audit))
print('residual range',min(r.get('residual_norm',np.inf) for r in audit),max(r.get('residual_norm',0) for r in audit))
print('coverage',[r for r in audit if 'failed_trial' in r])
