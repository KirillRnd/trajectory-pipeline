"""Mission descriptions shared by every stage; no mission values in solvers."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
import numpy as np
from .data import Scales, AU_M, MU_SUN, MU_EARTH, DAY_S
from .ephemerides import canonical, Ephemerides


def jd_tdb_from_calendar(value):
    """Interpret an explicitly labelled TDB calendar, without assuming UTC."""
    t = datetime.fromisoformat(value)
    if t.tzinfo is not None:
        raise ValueError('TDB calendar must not contain a UTC offset')
    return 2451545.0+(t-datetime(2000, 1, 1, 12)).total_seconds()/DAY_S


@dataclass
class Mission:
    case_id: str
    departure: str
    target: str
    launch_tdb: str
    tof_days: float
    center: str = 'Sun'
    mode: str = 'rendezvous'
    position_tolerance_m: float = 1000.
    velocity_tolerance_m_s: float = .01
    mass_kg: float = 156.
    departure_mode: str = 'bounded_norm'
    vinf_max_m_s: float = 3000.
    vinf_vector_m_s: list | None = None
    spacecraft: dict = field(default_factory=lambda: dict(thrust_N=.025, exhaust_velocity_m_s=20000., dry_mass_kg=90.))
    solver: dict = field(default_factory=dict)
    lunar: dict | None = None
    capture: dict | None = None
    arrival_offset_state_si: list | None = None

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        mission = cls(**data)
        mission.validate()
        return mission

    @property
    def launch_jd(self):
        return jd_tdb_from_calendar(self.launch_tdb)

    @property
    def arrival_jd(self):
        return self.launch_jd+self.tof_days

    def validate(self):
        def number(value):
            return isinstance(value,(int,float,np.integer,np.floating)) and not isinstance(value,(bool,np.bool_)) and np.isfinite(value)
        if not isinstance(self.case_id,str) or not self.case_id.strip():
            raise ValueError('case_id must be a nonempty string')
        for body in (self.departure, self.target, self.center):
            canonical(body)
        if self.mode not in ('rendezvous', 'flyby'):
            raise ValueError('mode must be rendezvous or flyby')
        values = [self.tof_days, self.position_tolerance_m, self.velocity_tolerance_m_s, self.mass_kg]
        if not all(number(value) for value in values) or min(values) <= 0:
            raise ValueError('Mission durations, tolerances and mass must be positive')
        required={'thrust_N','exhaust_velocity_m_s','dry_mass_kg'}
        if not isinstance(self.spacecraft,dict) or set(self.spacecraft)!=required:
            raise ValueError('spacecraft must contain exactly thrust_N, exhaust_velocity_m_s, dry_mass_kg; unknown engine fields are not ignored')
        hardware=[self.spacecraft[key] for key in sorted(required)]
        if not all(number(value) for value in hardware) or min(hardware)<=0:
            raise ValueError('Thrust, exhaust velocity and dry mass must be finite and positive')
        if self.spacecraft['dry_mass_kg']>=self.mass_kg:
            raise ValueError('Dry mass must be less than initial spacecraft mass')
        if not number(self.vinf_max_m_s) or self.vinf_max_m_s < 0:
            raise ValueError('Invalid departure excess limit')
        if self.departure_mode not in ('fixed_vector','fixed_norm','bounded_norm','free'):
            raise ValueError('Unknown departure mode')
        if self.departure_mode=='fixed_vector':
            vector=np.asarray(self.vinf_vector_m_s,dtype=float)
            if vector.shape!=(3,) or not np.isfinite(vector).all():
                raise ValueError('fixed_vector needs vinf_vector_m_s with three finite components')
        self.launch_jd
        if self.lunar is not None and (canonical(self.center)!='earth' or canonical(self.target)!='moon' or canonical(self.departure)!='earth'):
            raise ValueError('Lunar orbit specifications require Earth-centered Earth-to-Moon missions')
        if self.arrival_offset_state_si is not None:
            offset=self.arrival_offset_state_si
            if not isinstance(offset,list) or len(offset)!=6 or not all(number(x) for x in offset):
                raise ValueError('Arrival offset must contain six finite SI numbers')
            if self.mode!='rendezvous':raise ValueError('A resolved arrival state requires six fixed endpoint conditions')
        if self.capture is not None:
            from .planetary_capture import CaptureOrbit
            if canonical(self.center)!='sun' or self.mode!='rendezvous':raise ValueError('Planet capture requires a heliocentric fixed-state transfer')
            if canonical(self.target) in ('sun','moon'):raise ValueError('Solar and lunar capture are outside this planetary method')
            required=set(CaptureOrbit.__dataclass_fields__)
            if not isinstance(self.capture,dict) or not required<=set(self.capture) or set(self.capture)-required-{'plane','interface_side'}:
                raise ValueError('Capture needs all physical orbit dimensions and no unknown fields')
            if not all(number(self.capture[k]) for k in required):raise ValueError('Capture dimensions must be numbers')
            CaptureOrbit(**{k:self.capture[k] for k in required}).validate()
            if self.capture.get('plane','planet_orbit')!='planet_orbit' or self.capture.get('interface_side','sunward')!='sunward':
                raise ValueError('This capture interface currently supports the planet orbital plane and sunward apoapsis')
        return self

    def boundary(self, eph=None):
        self.validate()
        eph = eph or Ephemerides()
        if canonical(self.center) != 'sun':
            if canonical(self.center)=='earth' and self.lunar is not None:
                from .lunar import lunar_boundary
                return lunar_boundary(self,eph)
            raise ValueError('Earth-centered departures need explicit parking-orbit states and lunar dynamics, not Earth center as a point')
        initial = eph.state(self.departure, self.launch_jd, self.center)
        final = eph.state(self.target, self.arrival_jd, self.center)
        if self.arrival_offset_state_si is not None:final=final+np.asarray(self.arrival_offset_state_si)
        elif self.capture is not None:raise ValueError('Capture interface is unresolved; use the complete solve controller')
        scales = Scales(float(np.linalg.norm(initial[:3])), MU_SUN)
        return initial, final, scales

    def to_dict(self):
        result=asdict(self)
        # Preserve serialized/hash identity of all pre-capture missions.
        for key in ('capture','arrival_offset_state_si'):
            if result[key] is None:result.pop(key)
        return result
