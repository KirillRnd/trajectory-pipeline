"""Local, reversible ILTT parameter chart for the six spatial costates.

The parameters are [dm,j,Omega,omega,kappa,lambda]. This is a coordinate
change at a fixed physical state, NOT a call to T_a or a new ILTT entry.
Canonical costates take priority: an explicit additive offset makes the local
chart exact even outside the uncorrected ILTT approximation family.
"""
import numpy as np
from scipy.optimize import least_squares
from time import perf_counter
from .irt import _module


class ILTTCoordinates:
    names=('dm','j','Omega_rad','omega_rad','kappa','lambda')

    def __init__(self, initial, reference, *, dm_limit=.999*abs(np.sin(.642))):
        self.tb=_module('_pipeline_iltt','ILTT/ILTTToolbox.py')
        self.initial=np.asarray(initial,dtype=float)
        self.reference=np.asarray(reference,dtype=float).copy()
        if self.initial.shape!=(6,) or not np.isfinite(self.initial).all():raise ValueError('Expected normalized [r,v]')
        if self.reference.shape!=(6,) or not np.isfinite(self.reference).all():raise ValueError('Expected six ILTT parameters')
        if not np.isfinite(dm_limit) or not 0<dm_limit<1/np.cos(.642):raise ValueError('Invalid ILTT dm limit')
        self.dm_limit=float(dm_limit)
        self.costate_offset=np.zeros(6)
        self.frame=self.tb.calculate_R_matrix(self.initial[:3][None,:],self.initial[3:][None,:])
        if np.linalg.cond(self.frame)>1e12:raise ValueError('Singular initial orbital frame')
        self.phase=float(self.tb.rv2orb(self.initial[:3,None],self.initial[3:,None],1)[6][0])
        # Keep the approximation family local: the formulas change at lambda=.75.
        short=self.reference[5]<.75
        self.lower=np.array([-dm_limit,-30,self.reference[2]-np.pi,self.reference[3]-np.pi,.1,1e-8 if short else .75])
        self.upper=np.array([dm_limit,30,self.reference[2]+np.pi,self.reference[3]+np.pi,10,np.nextafter(.75,0) if short else np.inf])
        self.to_costates(self.reference)

    def to_costates(self,parameters):
        return self.formula(parameters)+self.costate_offset

    def formula(self,parameters):
        x=np.asarray(parameters,dtype=float)
        if x.shape!=(6,) or not np.isfinite(x).all() or np.any(x<self.lower) or np.any(x>self.upper):
            raise ValueError('ILTT parameters outside the declared chart; clipping forbidden')
        dm,j,node,peri,kappa,lam=x
        R=self.tb.calculate_RiO_matrix_noapprox(j,node-self.phase)@self.tb.calculate_Reo_matrix_noapprox(dm,peri-self.phase,dm_limit=self.dm_limit)@self.frame
        return np.concatenate(self.tb.apply_R(R,*self.tb.get_initial_adjoint(lam,kappa,1)))

    def jacobian(self,x):
        # Difference only the cheap algebraic map, never reintegrate the BVP.
        x=np.asarray(x,dtype=float);columns=[]
        for k in range(6):
            h=2e-6*max(1,abs(x[k]));a=x.copy();b=x.copy()
            a[k]=max(self.lower[k],x[k]-h);b[k]=min(self.upper[k],x[k]+h)
            columns.append((self.formula(b)-self.formula(a))/(b[k]-a[k]))
        return np.array(columns).T

    def from_costates(self,costates, *, guess=None, deadline=np.inf, tolerance=2e-11):
        p=np.asarray(costates,dtype=float)
        if p.shape!=(6,) or not np.isfinite(p).all():raise ValueError('Expected six finite costates')
        scale=max(float(np.linalg.norm(p)),1e-4)
        def residual(x):
            if perf_counter()>deadline:raise TimeoutError('ILTT inverse coordinate budget reached')
            return (self.to_costates(x)-p)/scale
        seed=self.reference if guess is None else np.asarray(guess,dtype=float)
        self.to_costates(seed)
        opt=least_squares(residual,seed,jac=lambda x:self.jacobian(x)/scale,
                          bounds=(self.lower,self.upper),x_scale='jac',max_nfev=300,
                          ftol=1e-13,xtol=1e-13,gtol=1e-13)
        fit_error=float(np.linalg.norm(self.to_costates(opt.x)-p))
        anchored=fit_error>tolerance*scale
        if anchored:
            # Never project or reject a physical solution because an empirical
            # ILTT family cannot represent it. Recenter at the declared local
            # reference (rather than at a saturated fit), retaining the offset.
            x=seed.copy()
            self.costate_offset=p-self.formula(x)
        else:
            x=opt.x
        error=float(np.linalg.norm(self.to_costates(x)-p))
        sv=np.linalg.svd(self.jacobian(x),compute_uv=False)
        return x,dict(costate_roundtrip_error=error,unanchored_fit_error=fit_error,
                      anchored=bool(anchored),costate_offset=self.costate_offset.tolist(),
                      nfev=int(opt.nfev),jacobian_singular_values=sv.tolist(),
                      local_rank=int(np.sum(sv>sv[0]*1e-10)))

    def record(self,parameters):
        return dict(version=1,initial_state_normalized=self.initial.tolist(),
                    reference=self.reference.tolist(),parameters=np.asarray(parameters).tolist(),
                    dm_limit=self.dm_limit,costate_offset=self.costate_offset.tolist(),
                    convention='p = ILTT(parameters, initial_state) + costate_offset; duration independent')

    @classmethod
    def restore(cls,record):
        if record.get('version')!=1:raise ValueError('Unknown ILTT chart version')
        result=cls(record['initial_state_normalized'],record['reference'],dm_limit=record['dm_limit'])
        offset=np.asarray(record['costate_offset'],dtype=float)
        if offset.shape!=(6,) or not np.isfinite(offset).all():raise ValueError('Invalid costate offset')
        result.costate_offset=offset.copy()
        result.to_costates(record['parameters'])
        return result
