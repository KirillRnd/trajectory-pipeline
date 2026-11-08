"""Versioned, pickle-free exchange format. Dimensional arrays are always SI."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import numpy as np

DAY_S = 86400.0
AU_M = 149597870700.0
MU_SUN = 1.32712440018e20
MU_EARTH = 3.986004356e14


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


@dataclass(frozen=True)
class Scales:
    distance_m: float
    mu_m3_s2: float

    def __post_init__(self):
        if not np.isfinite([self.distance_m, self.mu_m3_s2]).all() or min(self.distance_m, self.mu_m3_s2) <= 0:
            raise ValueError('Positive finite distance and gravitational parameter required')

    @property
    def time_s(self):
        return np.sqrt(self.distance_m**3 / self.mu_m3_s2)

    @property
    def velocity_m_s(self):
        return self.distance_m / self.time_s

    @property
    def acceleration_m_s2(self):
        return self.distance_m / self.time_s**2

    def normalize_state(self, rv):
        return np.asarray(rv, dtype=float) / np.r_[np.full(3, self.distance_m), np.full(3, self.velocity_m_s)]

    def dimensional_state(self, rv):
        return np.asarray(rv, dtype=float) * np.r_[np.full(3, self.distance_m), np.full(3, self.velocity_m_s)]


@dataclass
class Trajectory:
    metadata: dict
    arrays: dict

    def validate(self):
        for field in ('case_id', 'epoch_jd', 'time_scale', 'frame', 'center', 'model', 'status'):
            if field not in self.metadata:
                raise ValueError(f'Missing metadata: {field}')
        if self.metadata.get('schema_version', 1) != 1:
            raise ValueError('Unsupported trajectory schema')
        if self.metadata['time_scale'] != 'TDB':
            raise ValueError('Trajectory epochs must be explicitly converted to TDB')
        if not np.isfinite(self.metadata['epoch_jd']):
            raise ValueError('Nonfinite epoch')
        t = np.asarray(self.arrays['t_s'])
        n = len(t)
        if t.ndim != 1 or n < 2 or t[0] != 0 or not np.all(np.diff(t) > 0):
            raise ValueError('Time must increase strictly from zero')
        for key, value in self.arrays.items():
            a = np.asarray(value)
            if a.dtype.kind not in 'fiub' or not np.isfinite(a).all():
                raise ValueError(f'Non-numeric or nonfinite array: {key}')
        for key in ('r_m', 'v_m_s'):
            if np.shape(self.arrays[key]) != (n, 3):
                raise ValueError(f'{key} must have shape (n,3)')
        for key in ('mass_kg', 'thrust_N', 'active'):
            if key in self.arrays and np.shape(self.arrays[key]) != (n,):
                raise ValueError(f'{key} must have shape (n,)')
        if 'mass_kg' in self.arrays and np.min(self.arrays['mass_kg']) <= 0:
            raise ValueError('Mass must stay positive')
        if 'thrust_N' in self.arrays and np.min(self.arrays['thrust_N']) < 0:
            raise ValueError('Thrust magnitude must be nonnegative')
        if 'active' in self.arrays and not np.isin(self.arrays['active'], [False, True]).all():
            raise ValueError('Active flags must be boolean')
        return self

    def save(self, folder):
        self.validate()
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=False)
        np.savez_compressed(folder/'trajectory.npz', **self.arrays)
        meta = dict(self.metadata, schema_version=1,
                    arrays_sha256=sha256(folder/'trajectory.npz'))
        write_json(folder/'trajectory.json', meta)
        return folder

    @classmethod
    def load(cls, folder):
        folder = Path(folder)
        meta = json.loads((folder/'trajectory.json').read_text(encoding='utf-8'))
        if sha256(folder/'trajectory.npz') != meta['arrays_sha256']:
            raise ValueError('Trajectory file checksum mismatch')
        with np.load(folder/'trajectory.npz', allow_pickle=False) as data:
            arrays = {k: data[k] for k in data.files}
        return cls(meta, arrays).validate()
