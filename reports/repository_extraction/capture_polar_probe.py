import json
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from trajectory_pipeline.data import Scales,Trajectory
from trajectory_pipeline.planetary_capture import CaptureOrbit
from trajectory_pipeline.problem import Mission

def polar(inner,mission,rtol):
    orbit=CaptureOrbit(**inner.metadata['orbit'])
    scale=Scales(orbit.planet_radius_m+orbit.periapsis_altitude_m,orbit.mu_m3_s2)
    initial=np.r_[inner.arrays['r_m'][0],inner.arrays['v_m_s'][0]]
    rv=scale.normalize_state(initial)
    r=np.linalg.norm(rv[:3]);er=rv[:3]/r
    normal=np.cross(rv[:3],rv[3:]);normal/=np.linalg.norm(normal)
    et=np.cross(normal,er)
    h=np.linalg.norm(np.cross(rv[:3],rv[3:]))
    m0=inner.arrays['mass_kg'][0]
    F=mission.spacecraft['thrust_N'];c=mission.spacecraft['exhaust_velocity_m_s']
    A=F/m0/scale.acceleration_m_s2;q=F*scale.time_s/(m0*c)
    y=np.array([r,np.dot(rv[3:],er),h,0.,1.])
    times=inner.arrays['t_s']/scale.time_s
    edges=np.array([0,inner.metadata['burn_start_s'],inner.metadata['duration_s']])/scale.time_s
    out=np.empty((5,len(times)))
    for k,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
        if right<=left:continue
        def rhs(t,z):
            R,u,H,L,m=z
            return [u,H*H/R**3-1/R**2,-k*A*R/m,H/R**2,-k*q]
        sol=solve_ivp(rhs,(left,right),y,method='LSODA',rtol=rtol,atol=rtol/100,dense_output=True)
        assert sol.success
        mask=(times>=left)&(times<=right)
        out[:,mask]=sol.sol(times[mask]);y=sol.y[:,-1]
    r,u,h,L,m=out
    e_r=np.cos(L)[:,None]*er+np.sin(L)[:,None]*et
    e_t=-np.sin(L)[:,None]*er+np.cos(L)[:,None]*et
    state=np.c_[r[:,None]*e_r*scale.distance_m,(u[:,None]*e_r+(h/r)[:,None]*e_t)*scale.velocity_m_s]
    state[0]=initial
    dr=float(np.linalg.norm(state[:,:3]-inner.arrays['r_m'],axis=1).max())
    dv=float(np.linalg.norm(state[:,3:]-inner.arrays['v_m_s'],axis=1).max())
    return state,dict(rtol=rtol,position_error_m=dr,velocity_error_m_s=dv)

report=[]
for name,folder in [('capture','data/benchmarks/examples/earth_mars_2030_dec01_capture_400x30000'),
                    ('leo_capture','data/benchmarks/examples/earth_mars_2030_dec01_leo200_capture/match_05')]:
    inner=Trajectory.load(Path(folder)/'capture');mission=Mission.load(Path(folder)/'mission.json')
    previous=None
    for rtol in [3e-13,1e-13,3e-14]:
        state,row=polar(inner,mission,rtol);row['case']=name
        if previous is not None:
            row['change_position_m']=float(np.linalg.norm(state[:,:3]-previous[:,:3],axis=1).max())
            row['change_velocity_m_s']=float(np.linalg.norm(state[:,3:]-previous[:,3:],axis=1).max())
        previous=state;report.append(row)
print(json.dumps(report,indent=2))
Path('runs/capture_polar_probe.json').write_text(json.dumps(report,indent=2))
