"""Numerical replay with a different integrator and explicitly reported scope."""
import numpy as np
from scipy.integrate import solve_ivp
from .data import Scales


def replay_irt(initial, p, times,gravity_spec=None):
    """Independent numerical Hamiltonian replay; no optimizer callbacks."""
    if gravity_spec is not None:
        from .gravity import Gravity
        gravity=Gravity(gravity_spec)
    else:gravity=None
    def equations(t,y):
        r,v,pr,pv = y[:3],y[3:6],y[6:9],y[9:12]
        rho = np.linalg.norm(r)
        jac = (3*np.outer(r,r)/rho**2-np.eye(3))/rho**3
        g=-r/rho**3
        if gravity is not None:g,jac=gravity.independent_scalar(t,r)
        return np.r_[v,g+pv,-jac.T@pv,-pr]
    return solve_ivp(equations,(0,float(times[-1])),np.r_[initial,p],method='LSODA',
                     rtol=3e-12,atol=3e-14,t_eval=times,dense_output=gravity is not None)


def verify_irt(trajectory):
    trajectory.validate()
    m,a = trajectory.metadata,trajectory.arrays
    if m.get('stage') not in ('irt','departure'):
        raise ValueError('This verifier accepts IRT results only')
    scales = Scales(**m['scales'])
    initial = scales.normalize_state(m['initial_state_si'])
    target = scales.normalize_state(m['target_state_si'])
    p = np.asarray(m['costates_initial'])
    sol = replay_irt(initial,p,a['t_s']/scales.time_s,m.get('gravity_spec'))
    if not sol.success or len(sol.t)!=len(a['t_s']):
        return dict(passed=False,message='Independent replay did not reach arrival')
    rv = scales.dimensional_state(sol.y[:6].T)
    dr = np.linalg.norm(rv[-1,:3]-np.asarray(m['target_state_si'])[:3])
    dv = np.linalg.norm(rv[-1,3:]-np.asarray(m['target_state_si'])[3:])
    delta_r = np.linalg.norm(rv[:,:3]-a['r_m'],axis=1).max()
    delta_v = np.linalg.norm(rv[:,3:]-a['v_m_s'],axis=1).max()
    mission = m['mission']
    trans = float(np.linalg.norm(sol.y[9:12,-1]))
    passed = dr<=mission['position_tolerance_m']
    passed &= dv<=mission['velocity_tolerance_m_s'] if mission['mode']=='rendezvous' else trans<1e-8
    passed &= delta_r<=mission['position_tolerance_m'] and delta_v<=mission['velocity_tolerance_m_s']
    report=dict(passed=bool(passed),method='LSODA, independently implemented Hamiltonian RHS',
                position_residual_m=float(dr),velocity_residual_m_s=float(dv),
                trajectory_difference_m=float(delta_r),velocity_difference_m_s=float(delta_v),
                free_velocity_transversality=trans,
                scope='Numerical extremal and endpoint consistency; not proof of local/global optimality or N-body fidelity')
    if m.get('gravity_spec') is not None:
        from .gravity import Gravity
        clearance=Gravity(m['gravity_spec']).clearance_report(sol.sol,a['t_s']/scales.time_s)
        report.update(clearance=clearance,passed=bool(passed and clearance['passed']))
    return report
