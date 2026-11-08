"""Pazov mixed functional and its variable-mass constant-exhaust extension.

Normalized mass m/m0. Physical state: [r,v,m,p_r,p_v,p_m].
H = p_r*v + p_v*(g+A*d/m_eff) - beta*q*p_m*d - L_alpha,
L_alpha=(1-alpha)*(A*d)^2/2 + alpha*A*d,
m_eff=1+beta*(m-1), q=F*TU/(m0*c). At beta=1, alpha=1 the objective
equals c/VU times the expended mass fraction: exactly the same minimizers.
"""
from dataclasses import dataclass
import numpy as np
from components.pazov import OptimalControlSolver


@dataclass
class BoundedModel:
    a_max: float
    alpha: float = 0.
    beta: float = 0.
    q: float = 0.
    variable_mass: bool = False
    gravity_spec: dict | None = None

    def __post_init__(self):
        if not np.isfinite([self.a_max,self.alpha,self.beta,self.q]).all() or not self.a_max > 0 or not 0<=self.alpha<=1 or not 0<=self.beta<=1:
            raise ValueError('Invalid bounded-control model')
        if self.variable_mass and self.q<=0:raise ValueError('Variable-mass models require a positive fuel-flow coefficient')
        if not self.variable_mass and (self.beta!=0 or self.q!=0):raise ValueError('Mass homotopy coefficients require a variable-mass model')
        self.pazov=OptimalControlSolver(1.,self.a_max,self.alpha,'mixed')
        self.pazov.free_a_max=False
        if self.gravity_spec is not None:
            from .gravity import Gravity
            self.gravity=Gravity(self.gravity_spec)
        else:self.gravity=None

    @property
    def dimension(self):
        return 14 if self.variable_mass else 12

    @property
    def pv_slice(self):
        return slice(10,13) if self.variable_mass else slice(9,12)

    def split(self,y):
        if self.variable_mass:
            return y[:3],y[3:6],y[7:10],y[10:13],y[6],y[13]
        return y[:3],y[3:6],y[6:9],y[9:12],np.ones_like(y[0]),np.zeros_like(y[0])

    def switching(self,y):
        r,v,pr,pv,m,pm=self.split(y)
        effective_mass=1+self.beta*(m-1)
        return self.a_max*np.linalg.norm(pv,axis=0)/effective_mass-self.beta*self.q*pm-self.alpha*self.a_max

    def throttle(self,y):
        if not self.variable_mass:
            pv=y[self.pv_slice]
            if y.ndim==1:return np.clip(np.linalg.norm(self.pazov.optimal_control(pv))/self.a_max,0.,1.)
            u=self.pazov.optimal_control_array(np.atleast_2d(pv).reshape(3,-1))
            result=np.clip(np.linalg.norm(u,axis=0)/self.a_max,0.,1.)
            return result[0] if y.ndim==1 else result
        switch=self.switching(y)
        if self.alpha>=1-1e-12:
            return np.asarray(switch>0,dtype=float)
        return np.clip(switch/((1-self.alpha)*self.a_max**2),0,1)

    def rhs(self,t,y,throttle=None):
        r,v,pr,pv,m,pm=self.split(y)
        radius=np.linalg.norm(r,axis=0)
        mass=1+self.beta*(m-1)
        if np.any(mass<=0) or np.any(radius<1e-6):
            raise ValueError('Nonpositive mass or central collision during propagation')
        d=self.throttle(y) if throttle is None else throttle
        norm=np.linalg.norm(pv,axis=0)
        e=pv/np.maximum(norm,1e-15)
        acceleration=self.a_max*d/mass*e
        if self.gravity is not None:
            gravity,gradient=self.gravity.acceleration_gradient(t,r)
            pr_dot=-np.einsum('ij...,j...->i...',gradient,pv)
        else:
            gravity=-r/radius**3
            pr_dot=pv/radius**3-3*r*np.sum(r*pv,axis=0)/radius**5
        if self.variable_mass:
            return np.concatenate([v,gravity+acceleration,
                                   np.expand_dims(-self.beta*self.q*d,0),pr_dot,-pr,
                                   np.expand_dims(self.beta*self.a_max*d*norm/mass**2,0)],axis=0)
        return np.concatenate([v,gravity+acceleration,pr_dot,-pr],axis=0)


def origin_and_boundary(source,scales):
    """Recover the body's v0, not the already optimized spacecraft v0."""
    meta=source.metadata
    if 'body_initial_state_si' in meta:
        initial=np.asarray(meta['body_initial_state_si'],dtype=float)
    else:
        initial=np.asarray(meta['initial_state_si'],dtype=float).copy()
        if 'departure' in meta:
            initial[3:]-=meta['departure']['vector_m_s']
    return scales.normalize_state(initial),scales.normalize_state(meta['target_state_si'])


def boundary_residual(a,b,source,scales,model,face,*,kkt=False):
    body,target=origin_and_boundary(source,scales)
    mission=source.metadata['mission']
    mode=mission['departure_mode']
    pv=a[model.pv_slice]
    if mode=='free' or (mode=='bounded_norm' and face=='free'):
        departure=pv
    elif mode=='fixed_vector':
        vector=np.asarray(mission['vinf_vector_m_s'])/scales.velocity_m_s
        departure=a[3:6]-body[3:]-vector
    else:
        bound=mission['vinf_max_m_s']/scales.velocity_m_s
        dv=a[3:6]-body[3:]
        if kkt and bound:
            departure=np.r_[np.cross(pv,dv)/bound,(np.dot(dv,dv)-bound**2)/(2*bound)]
        else:
            departure=dv-bound*pv/max(np.linalg.norm(pv),1e-15) if bound else dv
    final=b[3:6]-target[3:] if mission['mode']=='rendezvous' else b[model.pv_slice]
    if model.variable_mass:
        return np.r_[a[:3]-body[:3],departure,a[6]-1,b[:3]-target[:3],final,b[13]]
    return np.r_[a[:3]-body[:3],departure,b[:3]-target[:3],final]
