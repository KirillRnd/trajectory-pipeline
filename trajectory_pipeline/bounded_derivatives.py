"""Analytic state derivatives of the central-field canonical equations.

The clipped control is differentiable inside each active/interior/coast region.
At a clipping boundary this selects the saturated-side derivative, as required
by a semismooth collocation step. No derivative of a moving bang-bang switch
is implied; exact switching times are still solved by the segmented corrector.
"""
import numpy as np


def canonical_jacobian(model,y,forced=None):
    if model.gravity is not None:
        raise ValueError('Analytic canonical derivatives require central gravity')
    scalar=y.ndim==1
    y=y[:,None] if scalar else y
    r,v,pr,pv,m,pm=model.split(y)
    n=y.shape[1]
    A,beta,q=model.a_max,model.beta,model.q
    M=1+beta*(m-1)
    R=np.linalg.norm(r,axis=0)
    P=np.linalg.norm(pv,axis=0)
    safe=np.maximum(P,1e-15)
    e=pv/safe
    eye=np.broadcast_to(np.eye(3)[:,:,None],(3,3,n))
    outer=lambda a,b:np.einsum('in,jn->ijn',a,b)
    G=3*outer(r,r)/R**5-eye/R**3
    dot=np.sum(r*pv,axis=0)
    curvature=(-3*(outer(pv,r)+outer(r,pv)+eye*dot)/R**5
               +15*outer(r,r)*dot/R**7)
    d=model.throttle(y) if forced is None else np.broadcast_to(forced,(n,))
    dp=np.zeros((3,n));dm=np.zeros(n);dz=np.zeros(n)
    if model.alpha<1-1e-12 and forced is None:
        denominator=(1-model.alpha)*A*A
        switch=model.switching(y)
        interior=(switch>0)&(switch<denominator)
        dp[:,interior]=A*e[:,interior]/M[interior]/denominator
        dm[interior]=-beta*A*P[interior]/M[interior]**2/denominator
        dz[interior]=-beta*q/denominator
    control_pv=A*d/M/safe*(eye-outer(e,e))+A/M*outer(e,dp)
    # At the real free-departure boundary p_v=0, the quadratic control
    # has the regular derivative I, despite its polar representation.
    if model.alpha==0 and forced is None:
        origin=(P<1e-14)&(np.abs(beta*q*pm)<1e-14)
        control_pv[:,:,origin]=eye[:,:,origin]/M[origin]**2
    j=np.zeros((model.dimension,model.dimension,n))
    pr_slice=slice(7,10) if model.variable_mass else slice(6,9)
    pv_slice=model.pv_slice
    j[:3,3:6]=eye
    j[3:6,:3]=G
    j[3:6,pv_slice]=control_pv
    j[pr_slice,:3]=curvature
    j[pr_slice,pv_slice]=-G
    j[pv_slice,pr_slice]=-eye
    if model.variable_mass:
        j[3:6,6]=A/M*e*dm-beta*A*d/M**2*e
        j[3:6,13]=A/M*e*dz
        j[6,pv_slice]=-beta*q*dp
        j[6,6]=-beta*q*dm
        j[6,13]=-beta*q*dz
        j[13,pv_slice]=beta*A/M**2*(d*e+P*dp)
        j[13,6]=beta*A*P/M**2*dm-2*beta**2*A*d*P/M**3
        j[13,13]=beta*A*P/M**2*dz
    return j[:,:,0] if scalar else j
