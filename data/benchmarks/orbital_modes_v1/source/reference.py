"""Import the accepted historical UMMP result; do not reoptimize its orbit."""
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from scipy.integrate import solve_ivp
from .data import Trajectory, DAY_S, sha256


def _kepler_samples(rv, times, mu):
    def rhs(t, y):
        return np.r_[y[3:6], -mu*y[:3]/np.linalg.norm(y[:3])**3]
    sol = solve_ivp(rhs, (0, float(times[-1])), rv, t_eval=times,
                    method='DOP853', rtol=2e-12, atol=1e-6)
    if not sol.success or len(sol.t) != len(times):
        raise RuntimeError(sol.message)
    return sol.y[:3].T


def import_ummp(path):
    path = Path(path)
    data = loadmat(path, simplify_cells=True)
    v, p, seed = data['verification'], data['param'], data['seed']
    t = np.asarray(v['t_sol'])
    y = np.asarray(v['Y_sol'])
    mu = float(p['mug'])
    year = np.linspace(0, 365.256363004*DAY_S, 700)
    earth0 = np.r_[seed['r0_m'], seed['v_earth_m_s']]
    target = np.r_[v['target_r_f'], v['target_v_f']]
    earth_arrival = _kepler_samples(earth0, np.array([0, float(t[-1])]), mu)[-1]
    return Trajectory(dict(case_id='ummp156_historical', epoch_jd=float(v['launch_jd']),
                           frame='ECLIPJ2000', center='Sun', time_scale='TDB',
                           model='legacy two-body ephemerides and UMMP power-dependent propulsion',
                           status='imported_reference', title='Траектория УММП 156 кг',
                           plot_limits=dict(x=[-1.58, 1.58], y=[-1.03, 1.33]),
                           source_file=path.name, source_sha256=sha256(path),
                           historical_verification=dict(position_residual_m=float(v['r_res_km'])*1000,
                                                        velocity_residual_m_s=float(v['v_res_m_s']),
                                                        fuel_kg=float(v['fuel_kg'])),
                           validation_note='Historical assertions copied, not a new independent verification. Overlays use the original two-body model, not JPL.',
                           overlays=[dict(array='earth_orbit_m', label='Орбита Земли', color='.82', linestyle=':'),
                                     dict(array='target_orbit_m', label='Орбита Апофиса', color='.68', linestyle='-.')],
                           markers=[dict(label='Земля, старт', r_m=earth0[:3].tolist()),
                                    dict(label='Земля, прибытие', r_m=earth_arrival.tolist(), hollow=True),
                                    dict(label='Апофис', r_m=target[:3].tolist(), color='#e00b0b', role='target')]),
                      dict(t_s=t, r_m=y[:, :3], v_m_s=y[:, 3:6],
                           mass_kg=float(p['m0'])-y[:, 6], thrust_N=np.asarray(v['thrust_N']),
                           active=np.asarray(v['thrust_N']) > 1e-9,
                           legacy_costates=y[:, 7:14], switching_function=np.asarray(v['switch_function']),
                           earth_orbit_m=_kepler_samples(earth0, year, mu),
                           target_orbit_m=_kepler_samples(target, year, mu))).validate()
