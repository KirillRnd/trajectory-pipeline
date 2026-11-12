"""Explicit per-body orbit sources; frozen Kepler models never switch at a date."""
import csv
import io
import numpy as np
from .ephemerides import Ephemerides, canonical, ROOT
from .data import DAY_S, AU_M, sha256

PRESETS = {
    'Apophis': ('apophis', 'apophis_horizons_elements_pre_2029-03-01.txt'),
    'ApophisNew': ('apophis', 'apophis_horizons_elements_post_2029-05-01.txt'),
    'EarthSimple': ('earth', None),
}


def preset_elements(name):
    body, filename = PRESETS[name]
    if filename is None:
        return dict(epoch_jd=2457390.5, a_m=AU_M, e=.01682781268763978,
                    i_deg=.002312212390408654, node_deg=219.8210990481491,
                    peri_deg=241.9337242483841, M_deg=float(np.rad2deg(.04600206682616619)),
                    mu_m3_s2=1.3271243994e20)
    path = ROOT/'data/orbits'/filename
    row = next(r for r in csv.reader(io.StringIO(path.read_text().split('$$SOE')[1].split('$$EOE')[0])) if r and r[0].strip())
    return dict(epoch_jd=float(row[0]), a_m=float(row[11])*1000, e=float(row[2]),
                i_deg=float(row[4]), node_deg=float(row[5]), peri_deg=float(row[6]),
                M_deg=float(row[9]), mu_m3_s2=1.3271244004127939e20)


def validate_sources(sources):
    if sources is None:return
    if not isinstance(sources, dict):raise ValueError('orbit_sources must be a per-body object')
    seen=set()
    for body, spec in sources.items():
        key=canonical(body)
        if key in seen:raise ValueError('Duplicate orbit source body')
        seen.add(key)
        if spec == {'kind':'ephemerides'}:continue
        if not isinstance(spec,dict) or spec.get('kind')!='kepler':raise ValueError('Unknown orbit source')
        if set(spec)=={'kind','preset'}:
            if spec['preset'] not in PRESETS or PRESETS[spec['preset']][0]!=key:raise ValueError('Preset/body mismatch')
            el=preset_elements(spec['preset'])
        elif set(spec)=={'kind','elements'}:el=spec['elements']
        else:raise ValueError('Kepler source requires exactly preset or elements')
        fields={'epoch_jd','a_m','e','i_deg','node_deg','peri_deg','M_deg','mu_m3_s2'}
        if not isinstance(el,dict) or set(el)!=fields:raise ValueError('Invalid Kepler element fields')
        if not all(type(v) in (float,int) and np.isfinite(v) for v in el.values()):raise ValueError('Nonfinite Kepler elements')
        if not (el['a_m']>0 and el['mu_m3_s2']>0 and 0<=el['e']<1 and 0<=el['i_deg']<=180):raise ValueError('Expected elliptic Kepler elements')


def kepler_state(el, epochs):
    a,e=el['a_m'],el['e'];n=np.sqrt(el['mu_m3_s2']/a**3)
    M=(np.deg2rad(el['M_deg'])+(epochs-el['epoch_jd'])*DAY_S*n+np.pi)%(2*np.pi)-np.pi
    E=M.copy()
    for _ in range(50):
        step=(E-e*np.sin(E)-M)/(1-e*np.cos(E));E-=step
        if np.max(np.abs(step))<1e-13:break
    if np.max(np.abs(E-e*np.sin(E)-M))>1e-12:raise ValueError('Kepler equation did not converge')
    root=np.sqrt(1-e*e);den=1-e*np.cos(E)
    r=np.c_[a*(np.cos(E)-e),a*root*np.sin(E),np.zeros_like(E)]
    v=np.c_[-a*n*np.sin(E)/den,a*n*root*np.cos(E)/den,np.zeros_like(E)]
    O,w,i=np.deg2rad([el['node_deg'],el['peri_deg'],el['i_deg']])
    def rz(x):return np.array([[np.cos(x),-np.sin(x),0],[np.sin(x),np.cos(x),0],[0,0,1]])
    rx=np.array([[1,0,0],[0,np.cos(i),-np.sin(i)],[0,np.sin(i),np.cos(i)]])
    rot=rz(O)@rx@rz(w)
    return np.c_[r@rot.T,v@rot.T]


class OrbitSources(Ephemerides):
    def __init__(self,sources):
        super().__init__();validate_sources(sources)
        self.sources={canonical(k):v for k,v in (sources or {}).items()}

    def elements(self,key):
        spec=self.sources.get(key,{'kind':'ephemerides'})
        if spec['kind']=='ephemerides':return None
        return preset_elements(spec['preset']) if 'preset' in spec else spec['elements']

    def _heliocentric(self,body,epochs):
        el=self.elements(canonical(body))
        return super()._heliocentric(body,epochs) if el is None else kepler_state(el,epochs)

    def coverage(self,body):
        key=canonical(body);el=self.elements(key)
        if el is None:return super().coverage(body)
        spec=self.sources[key]
        result=dict(body=key,source='frozen_kepler',selection=spec,elements=el,
                    center='Sun',frame='ECLIPJ2000',time_scale='TDB',units='m,m/s',
                    start_jd=-1e9,stop_jd=1e9,
                    scope='Mathematical propagation domain, NOT physical validity across encounters')
        if 'preset' in spec and PRESETS[spec['preset']][1]:
            result['raw_sha256']=sha256(ROOT/'data/orbits'/PRESETS[spec['preset']][1])
        return result
