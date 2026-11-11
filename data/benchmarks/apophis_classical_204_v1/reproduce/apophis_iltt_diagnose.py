import json,sys,time,subprocess,concurrent.futures
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches
from trajectory_pipeline.data import DAY_S,write_json

ROOT=Path('runs/apophis_classical_204');ROOT.mkdir(exist_ok=True)
def worker(date,variant):
    raw=next(x for x in json.loads(Path('configs/search_matrix_date_v4.json').read_text()) if x['target']=='Apophis')
    raw.update(case_id='apophis_'+date[:10],launch_tdb=date,mass_kg=204)
    raw['spacecraft']=dict(thrust_N=.036,exhaust_velocity_m_s=1200*9.80665,dry_mass_kg=140)
    m=Mission(**raw).validate();tb,eph,scale,initial,el,phase,branches=angular_branches(m)
    b=branches[0];lam=b['lambda_initial'];kappa=float(el[0]);start=time.perf_counter()
    F,x0=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],lam,kappa,0,1,float(el[2]),float(el[3]),float(el[1]),float(el[8]))
    base=F(x0);h=1e-5;xp=x0.copy();xp[0]+=h;shift=F(xp)
    rec=dict(date=date,variant=variant,phase=float(phase),branch=b,x0=x0.tolist(),original_dm_endpoint_derivative=float(np.linalg.norm(np.r_[shift['rf']-base['rf'],shift['vf']-base['vf']])/h))
    path=ROOT/(date[:10]+'_'+variant+'.json');write_json(path,rec)
    limit=.999*abs(np.sin(.642))
    if variant=='extended':
        limit=.999/abs(np.cos(.642))
        def reo(dm,omega):
            theta=.642;e=dm*np.cos(theta);a=1-dm*np.sin(theta)
            denominator=a*(1-e*e)
            if denominator<=0:raise ValueError('nonelliptic R parameter')
            R=np.diag([a*(1-e),(1+e)/np.sqrt(denominator),(1+e)/np.sqrt(denominator)*a*(1-e)])
            angle=omega/2+np.sin(2*omega)/6+np.sin(4*omega)/32
            C=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
            return C@R@C.T
        tb.calculate_Reo_matrix_noapprox=reo
    upper=.5*(lam+branches[1]['lambda_initial']);lower=1e-4
    lo=np.array([-limit,-30,-np.inf,-np.inf,.1,lower]);hi=np.array([limit,30,np.inf,np.inf,10,upper])
    x=np.clip(x0,lo+1e-7,hi-1e-7);calls=0;best=np.inf
    def fun(x):
        nonlocal calls,best
        if time.perf_counter()-start>90:raise TimeoutError('90s correction budget')
        duration=2*np.pi*tb.T_a(x[5],x[4])*scale.time_s/DAY_S
        actual=F(x);target=scale.normalize_state(eph.state(m.target,m.launch_jd+duration,m.center))
        ae=np.array([float(a[0]) for a in tb.rv2orb(actual['rf'][:,None],actual['vf'][:,None],1)])
        de=np.array([float(a[0]) for a in tb.rv2orb(target[:3,None],target[3:,None],1)])
        residual=np.r_[de[[0,2,1]]-ae[[0,2,1]],tb.ang_err(de[[3,8,6]],ae[[3,8,6]])]
        calls+=1
        if np.linalg.norm(residual)<best:
            best=float(np.linalg.norm(residual));rec.update(best=best,x=x.tolist(),duration=float(duration),calls=calls,elapsed=time.perf_counter()-start);write_json(path,rec)
        return residual
    try:
        result=least_squares(fun,x,bounds=(lo,hi),x_scale='jac',diff_step=1e-5,max_nfev=180,ftol=1e-11,xtol=1e-11,gtol=1e-11)
        rec.update(status='resolved' if np.linalg.norm(result.fun)<1e-7 else 'partial',message=result.message)
    except Exception as exc:rec.update(status='failed',error=str(exc))
    write_json(path,rec);print(date,variant,rec.get('status'),rec.get('best'),flush=True)

if len(sys.argv)>1:worker(sys.argv[1],sys.argv[2])
else:
    jobs=[(d,v) for d in ['2028-05-20T12:00:00','2029-02-14T12:00:00','2029-08-13T12:00:00','2030-01-01T00:00:00'] for v in ['bounded','extended']]
    def launch(job):
        try:subprocess.run([sys.executable,__file__,*job],timeout=105,check=True)
        except Exception as exc:print(job,type(exc).__name__,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(launch,jobs))
