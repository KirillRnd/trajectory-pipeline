"""Rebuild the 156 kg Apophis benchmark at the archived boundary states."""
import argparse
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from .data import DAY_S, Scales, Trajectory, sha256, write_json
from .departure import run_departure
from .irt import solve_irt
from .pazov import run_pazov
from .problem import Mission
from .psi import run_psi
from .ummp import run_ummp
from .verification import verify_irt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/references'
MAT = DATA/'apophis_ummp_156kg_hard_bangbang_verified.mat'


class HistoricalBoundaries:
    """Supply only the two frozen boundary states and reference plot overlays."""

    def __init__(self):
        self.trajectory = Trajectory.load(DATA/'ummp156')
        self.identity = sha256(MAT)
        if self.identity != self.trajectory.metadata['source_sha256']:
            raise ValueError('Historical MAT checksum differs from the imported reference')
        reference = loadmat(MAT,simplify_cells=True)
        self.saved = reference['verification']
        seed = reference['seed']
        self.mu = float(reference['param']['mug'])
        self.mass = float(reference['param']['m0'])
        self.states = {
            'Earth': (self.saved['launch_jd'], np.r_[seed['r0_m'],seed['v_earth_m_s']], 'earth_orbit_m'),
            'Apophis': (self.saved['arrival_jd'], np.r_[self.saved['target_r_f'],self.saved['target_v_f']],
                        'target_orbit_m'),
        }
        self.excess = seed['v0_m_s']-seed['v_earth_m_s']

    def state(self, name, epoch, center):
        date,state,overlay = self.states[name]
        if np.ndim(epoch)==0:
            if center!='Sun' or abs(epoch-date)>1e-9:
                raise ValueError('Request outside the two frozen historical boundaries')
            return state.copy()
        positions = self.trajectory.arrays[overlay]
        return np.c_[positions,np.zeros_like(positions)]

    def coverage(self, name):
        return dict(reference_sha256=self.identity, epoch_jd=self.states[name][0],
                    scope='frozen historical boundary and plot overlay')


class HistoricalMission(Mission):
    def boundary(self,eph):
        initial,target,scales = super().boundary(eph)
        return initial,target,Scales(scales.distance_m,eph.mu)


def run_benchmark(output):
    boundaries = HistoricalBoundaries()
    base = Trajectory.load(ROOT/'data/benchmarks/psi/earth_apophis_2029')
    mission = HistoricalMission(**dict(base.metadata['mission'], case_id='apophis_156kg_historical_boundary',
                                      departure_mode='fixed_vector', vinf_vector_m_s=boundaries.excess.tolist(),
                                      tof_days=float(boundaries.saved['tof_days']), mass_kg=boundaries.mass))
    output = Path(output)
    output.mkdir(parents=True,exist_ok=False)
    source,summary = solve_irt(mission,boundaries)
    if source is None:
        raise RuntimeError(f'Historical geometry IRT failed: {summary}')
    check = verify_irt(source)
    if not check['passed']:
        raise RuntimeError(f'Historical geometry IRT failed verification: {check}')
    source.metadata.update(status='verified_extremal',verification=check,boundary_reference_sha256=boundaries.identity)
    source.save(output/'irt')
    source = Trajectory.load(output/'irt')

    for stage,solver,kwargs in (('departure',run_departure,{}), ('pazov',run_pazov,{'target_alpha':.5}), ('psi',run_psi,{})):
        folder = output/stage
        _,state = solver(source,folder,**kwargs)
        if state['status']!='completed_stage':
            raise RuntimeError(f'Historical geometry {stage} stopped: {state}')
        source = Trajectory.load(folder/(state['last_point'] if stage=='departure' else state['last_result']))

    result,state = run_ummp(source,output/'ummp')
    report = dict(status=state['status'], historical_mat_sha256=boundaries.identity,
                  psi_fuel_kg=source.metadata['verification']['fuel_kg'], psi_arrays_sha256=source.metadata['arrays_sha256'],
                  historical_fuel_kg=float(boundaries.saved['fuel_kg']), last_result='ummp/'+state['last_result'],
                  reached_fraction=state['reached_fraction'])
    if state['status']=='completed_stage':
        historical_intervals = np.asarray(boundaries.saved['active_intervals_days'])
        edges = np.r_[0.,result.metadata['switch_times_s'],result.arrays['t_s'][-1]]/DAY_S
        first = int(result.metadata['initial_throttle'])
        on = np.flatnonzero((np.arange(len(edges)-1)+first)%2)
        active_intervals = np.c_[edges[on],edges[on+1]]
        check = state['verification']
        report.update(verification=check, fuel_difference_kg=check['fuel_kg']-report['historical_fuel_kg'],
                      historical_active_intervals_days=historical_intervals.tolist(),
                      active_intervals_days=active_intervals.tolist(),
                      historical_position_residual_m=float(boundaries.saved['r_res_km']*1000),
                      historical_velocity_residual_m_s=float(boundaries.saved['v_res_m_s']))
    write_json(output/'summary.json',report)
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    result = run_benchmark(parser.parse_args().output)
    print(result)
    raise SystemExit(0 if result['status']=='completed_stage' else 2)
