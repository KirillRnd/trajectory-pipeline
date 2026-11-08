"""Point-mass central/third-body dynamics in a translating inertial frame.

Third-body positions are interpolated from an immutable local ephemeris table.
The indirect acceleration of the coordinate origin is included explicitly.
"""
from functools import lru_cache
from pathlib import Path
import json
import hashlib
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from scipy.optimize import minimize_scalar
from .data import DAY_S,sha256,write_json
from .ephemerides import Ephemerides

ROOT=Path(__file__).resolve().parents[1]
MU_MOON=4.902800066e12
MU_SUN=1.32712440018e20


def prepare_lunar_ephemerides(mission,scales):
    from importlib.metadata import version
    settings=dict(epoch_jd=mission.launch_jd,tof_s=mission.tof_days*DAY_S,
                  step_s=float(mission.lunar.get('ephemeris_step_s',900)),
                  source='KIAM bundled JPLEPH',package_version=version('kiam-astro'),
                  center='Earth',frame='ECLIPJ2000',time_scale='TDB')
    if not 1<=settings['step_s']<=3600:raise ValueError('Lunar ephemeris step must be 1..3600 seconds')
    key=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()[:16]
    folder=ROOT/'data/lunar_ephemerides'/key
    if not (folder/'metadata.json').exists():
        eph=Ephemerides()
        count=int(np.ceil(settings['tof_s']/settings['step_s']))+1
        t=np.linspace(0,settings['tof_s'],count)
        epochs=mission.launch_jd+t/DAY_S
        moon=eph.state('Moon',epochs,'Earth')
        sun=eph.state('Sun',epochs,'Earth')
        folder.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(folder/'vectors.npz',t_s=t,moon_state_si=moon,sun_state_si=sun)
        write_json(folder/'metadata.json',dict(settings,arrays_sha256=sha256(folder/'vectors.npz')))
    metadata=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    return dict(kind='earth_moon_sun',ephemeris_file=(folder/'vectors.npz').relative_to(ROOT).as_posix(),
                ephemeris_sha256=metadata['arrays_sha256'],epoch_jd=mission.launch_jd,
                distance_m=scales.distance_m,time_s=scales.time_s,mu_m3_s2=scales.mu_m3_s2,
                moon_mu_ratio=MU_MOON/scales.mu_m3_s2,sun_mu_ratio=MU_SUN/scales.mu_m3_s2,
                perturbation_scale=1.,earth_min_radius_m=6378136.3+float(mission.lunar.get('earth_clearance_m',200000)),
                moon_min_radius_m=1737400.+float(mission.lunar.get('moon_clearance_m',100000)),
                ephemeris_source=settings)


@lru_cache(maxsize=32)
def _splines(filename,digest,distance,time):
    path=ROOT/filename
    if sha256(path)!=digest:raise ValueError('Lunar ephemeris table checksum mismatch')
    with np.load(path,allow_pickle=False) as a:
        t=a['t_s']/time
        out=[]
        for key in ('moon_state_si','sun_state_si'):
            s=a[key]
            out.append(CubicHermiteSpline(t,s[:,:3]/distance,s[:,3:]*time/distance,extrapolate=False))
    return tuple(out),float(t[-1])


class Gravity:
    def __init__(self,spec):
        self.spec=spec
        if spec['kind']!='earth_moon_sun':raise ValueError('Unknown noncentral gravity model')
        self.scale=float(spec.get('perturbation_scale',1.))
        if not 0<=self.scale<=1:raise ValueError('Gravity continuation parameter outside [0,1]')
        self.splines,self.duration=_splines(spec['ephemeris_file'],spec['ephemeris_sha256'],spec['distance_m'],spec['time_s'])

    def positions(self,t):
        values=np.asarray(t,dtype=float)
        if np.any(values<-1e-10) or np.any(values>self.duration+1e-10):raise ValueError('Gravity time outside local ephemeris coverage')
        values=np.clip(values,0,self.duration)
        return tuple(s(values).T for s in self.splines)

    def acceleration_gradient(self,t,r):
        radius=np.linalg.norm(r,axis=0)
        g=-r/radius**3
        outer=np.einsum('i...,j...->ij...',r,r)
        identity=np.eye(3).reshape((3,3)+(1,)*(r.ndim-1))
        gradient=3*outer/radius**5-identity/radius**3
        if self.scale:
            for R,mu in zip(self.positions(t),(self.spec['moon_mu_ratio'],self.spec['sun_mu_ratio'])):
                if R.ndim<r.ndim:R=R[:,None]
                d=R-r
                rho=np.linalg.norm(d,axis=0)
                Rnorm=np.linalg.norm(R,axis=0)
                if np.any(rho<1e-8):raise ValueError('Third-body singularity')
                g+=self.scale*mu*(d/rho**3-R/Rnorm**3)
                gradient+=self.scale*mu*(3*np.einsum('i...,j...->ij...',d,d)/rho**5-identity/rho**3)
        return g,gradient

    def independent_scalar(self,t,r):
        """Separate scalar formulation for forward verification."""
        radius=float(np.linalg.norm(r))
        acceleration=-r/radius**3
        jacobian=(3*np.outer(r,r)/radius**2-np.eye(3))/radius**3
        if self.scale:
            moon,sun=self.positions(float(t))
            for position,parameter in ((moon,self.spec['moon_mu_ratio']),(sun,self.spec['sun_mu_ratio'])):
                relative=r-position
                distance=float(np.linalg.norm(relative))
                origin_distance=float(np.linalg.norm(position))
                acceleration-=self.scale*parameter*(relative/distance**3+position/origin_distance**3)
                jacobian+=self.scale*parameter*(3*np.outer(relative,relative)/distance**2-np.eye(3))/distance**3
        return acceleration,jacobian

    def clearances(self,t,r):
        moon,_=self.positions(t)
        return np.linalg.norm(r,axis=0)*self.spec['distance_m'],np.linalg.norm(r-moon,axis=0)*self.spec['distance_m']

    def clearance_report(self,state_at,times):
        grid=np.unique(np.r_[times,np.linspace(0,times[-1],max(1001,len(times)*2))])
        r=state_at(grid)[:3]
        values=self.clearances(grid,r)
        minima=[]
        for body,distances in enumerate(values):
            best=float(np.min(distances))
            local=np.flatnonzero((distances[1:-1]<=distances[:-2])&(distances[1:-1]<=distances[2:]))+1
            for index in local:
                def distance(t):
                    return float(self.clearances(float(t),state_at(float(t))[:3])[body])
                fit=minimize_scalar(distance,bounds=(grid[index-1],grid[index+1]),method='bounded',options={'xatol':1e-10})
                best=min(best,float(fit.fun))
            minima.append(best)
        enforced=self.scale>=1-1e-12
        passed=minima[0]>=self.spec['earth_min_radius_m'] and minima[1]>=self.spec['moon_min_radius_m']
        return dict(passed=bool(passed or not enforced),collision_constraints_enforced=enforced,
                    minimum_geocentric_radius_m=minima[0],minimum_selenocentric_radius_m=minima[1],
                    required_geocentric_radius_m=self.spec['earth_min_radius_m'],required_selenocentric_radius_m=self.spec['moon_min_radius_m'])
