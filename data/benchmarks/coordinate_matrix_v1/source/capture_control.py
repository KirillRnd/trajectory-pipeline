"""Explicit angular capture policy; angles are radians, states are Cartesian.

This contract is independent of the legacy MATLAB control_type convention.
Used by the event-resolved capture integrator and orbital mission controller.
"""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class CaptureControl:
    mode: str = 'continuous'
    phase_reference: str = 'periapsis'
    half_width_rad: float = math.pi
    eccentricity_slope_rad: float = 0.
    phase_offset_rad: float = 0.
    circular_eccentricity: float = 1e-8

    def validate(self):
        if self.mode not in ('continuous', 'angular'):
            raise ValueError('Unknown capture control mode')
        if self.phase_reference not in ('periapsis', 'fixed_axis'):
            raise ValueError('Unknown capture phase reference')
        values = [self.half_width_rad, self.eccentricity_slope_rad,
                  self.phase_offset_rad, self.circular_eccentricity]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError('Capture angles and eccentricity threshold must be finite numbers')
        if not 0 < self.circular_eccentricity < 1:
            raise ValueError('Circular eccentricity threshold must lie between zero and one')
        if self.mode == 'angular' and not 0 < self.half_width_rad <= math.pi:
            raise ValueError('Angular half width must lie in (0, pi]')
        if self.mode == 'angular' and not (self.half_width_rad == math.pi and self.eccentricity_slope_rad == 0):
            endpoints=(self.half_width_rad,self.half_width_rad+self.eccentricity_slope_rad)
            if min(endpoints)<1e-3 or max(endpoints)>math.pi-1e-3:
                raise ValueError('Angular law must stay in [0.001, pi-0.001] over elliptic e in [0,1], or be exactly pi')
        if self.mode == 'continuous' and (self.half_width_rad != math.pi or self.eccentricity_slope_rad != 0 or self.phase_offset_rad != 0):
            raise ValueError('Continuous capture does not accept unused angular settings')
        return self

    def margin(self, state, mu, reference_axis):
        """Positive inside the gate; reference_axis must rotate with the orbit.

        Near circularity, periapsis has no reliable direction: use fixed_axis
        explicitly. No implicit change of policy or global Cartesian x-axis.
        Invalid widths on an encountered eccentricity fail, rather than clip.
        """
        self.validate()
        if self.mode == 'continuous':
            return 1.
        state = np.asarray(state, dtype=float)
        axis = np.asarray(reference_axis, dtype=float)
        if state.shape != (6,) or axis.shape != (3,) or not np.all(np.isfinite(np.r_[state, axis])) or not math.isfinite(mu) or mu <= 0:
            raise ValueError('Invalid capture state, gravity or reference axis')
        r, v = state[:3], state[3:]
        radius = np.linalg.norm(r)
        h = np.cross(r, v)
        hn = np.linalg.norm(h)
        if radius <= 0 or hn <= 0:
            raise ValueError('Angular control requires a nonradial orbit')
        normal = h / hn
        eccentricity_vector = np.cross(v, h) / mu - r / radius
        eccentricity = np.linalg.norm(eccentricity_vector)
        width = self.half_width_rad + self.eccentricity_slope_rad * eccentricity
        if not 0 < width <= math.pi:
            raise ValueError('Angular width outside (0, pi] on the current orbit')
        if self.phase_reference == 'periapsis':
            if eccentricity < self.circular_eccentricity:
                raise ValueError('Undefined periapsis; choose fixed_axis for near-circular orbits')
            axis = eccentricity_vector
        axis = axis - normal * np.dot(axis, normal)
        length = np.linalg.norm(axis)
        if length < 1e-14:
            raise ValueError('Reference axis must have an orbital-plane projection')
        axis = axis / length
        phase = math.atan2(np.dot(r, np.cross(normal, axis)), np.dot(r, axis))
        phase = math.remainder(phase - self.phase_offset_rad, 2 * math.pi)
        return width - abs(phase)

    def throttle(self, state, mu, reference_axis):
        return float(self.margin(state, mu, reference_axis) >= 0)


def validate_capture_options(arrival):
    control=arrival.get('capture_control')
    if control is not None:
        if not isinstance(control,dict) or set(control)-set(CaptureControl.__dataclass_fields__):
            raise ValueError('Unknown capture_control flag')
        CaptureControl(**control).validate()
    for key in ('max_capture_days','arrival_propellant_budget_kg','spacecraft_propellant_budget_kg'):
        if key in arrival:
            value=arrival[key]
            if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<=0:
                raise ValueError(key+' must be finite and positive')
    search=arrival.get('duration_search')
    if search is not None:
        if not isinstance(search,dict) or set(search)!={'half_widths_rad'}:
            raise ValueError('duration_search requires exactly half_widths_rad')
        if control is None or control.get('mode')!='angular':
            raise ValueError('duration_search requires angular capture_control')
        if not any(k in arrival for k in ('arrival_propellant_budget_kg','spacecraft_propellant_budget_kg')):
            raise ValueError('duration_search requires an explicit propellant budget')
        widths=search['half_widths_rad']
        if not isinstance(widths,list) or not widths or len(widths)>32:
            raise ValueError('duration_search needs 1..32 declared candidate widths')
        for width in widths:
            CaptureControl(**dict(control,half_width_rad=width)).validate()
        if len(set(widths))!=len(widths):raise ValueError('Duplicate duration_search candidates')


def capture_budget_check(arrival,initial_mass,entry_mass,final_mass,duration_s):
    checks={
        'capture_duration':duration_s<=arrival.get('max_capture_days',2000.)*86400+1e-6,
        'arrival_propellant':entry_mass-final_mass<=arrival.get('arrival_propellant_budget_kg',math.inf)+1e-6,
        'spacecraft_propellant':initial_mass-final_mass<=arrival.get('spacecraft_propellant_budget_kg',math.inf)+1e-6,
    }
    return dict(passed=all(checks.values()),checks=checks)


def apply_capture_flags(mission,args):
    """CLI overrides become the saved, hashed physical request, never globals."""
    from copy import deepcopy
    from dataclasses import replace
    keys=('capture_mode','capture_half_width_deg','capture_phase_reference','capture_eccentricity_slope_deg',
          'capture_phase_offset_deg','capture_search_widths_deg','capture_fuel_budget_kg','spacecraft_fuel_budget_kg','capture_max_days')
    values={key:getattr(args,key,None) for key in keys}
    if all(v is None for v in values.values()):return mission
    modes=deepcopy(mission.orbital_maneuvers)
    if not modes or modes['arrival']['kind']!='spiral':raise ValueError('Capture flags require orbital_maneuvers.arrival.kind=spiral')
    a=modes['arrival'];control=deepcopy(a.get('capture_control',{}))
    for key,field in [('capture_mode','mode'),('capture_phase_reference','phase_reference')]:
        if values[key] is not None:control[field]=values[key]
    for key,field in [('capture_half_width_deg','half_width_rad'),('capture_eccentricity_slope_deg','eccentricity_slope_rad'),('capture_phase_offset_deg','phase_offset_rad')]:
        if values[key] is not None:control[field]=math.radians(values[key])
    if control:a['capture_control']=control
    if values['capture_search_widths_deg'] is not None:
        a['duration_search']={'half_widths_rad':[math.radians(x) for x in values['capture_search_widths_deg']]}
    for key,field in [('capture_fuel_budget_kg','arrival_propellant_budget_kg'),('spacecraft_fuel_budget_kg','spacecraft_propellant_budget_kg'),('capture_max_days','max_capture_days')]:
        if values[key] is not None:a[field]=values[key]
    result=replace(mission,orbital_maneuvers=modes);result.validate()
    return result
