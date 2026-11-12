"""Offline KIAM/JPL major bodies and locally cached Horizons small bodies.

Public states: geometric, ECLIPJ2000 axes, specified center, SI, JD TDB.
Network access occurs only in the explicit download command.
"""
from functools import lru_cache
from pathlib import Path
import csv
import io
import json
import threading
import struct
import urllib.parse
import urllib.request
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from .data import DAY_S, sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'data/ephemerides'
API = 'https://ssd.jpl.nasa.gov/api/horizons.api'
MAJOR = {'sun': ('Sun', '10'), 'mercury': ('Mercury', '199'),
         'venus': ('Venus', '299'), 'earth': ('Earth', '399'),
         'moon': ('Moon', '301'), 'mars': ('Mars', '499'),
         'jupiter': ('Jupiter', '599'), 'saturn': ('Saturn', '699'),
         'uranus': ('Uranus', '799'), 'neptune': ('Neptune', '899'),
         'pluto': ('Pluto', '999')}
ASTEROIDS = {'apophis': '99942;', 'eros': '433;', 'bennu': '101955;',
             'ryugu': '162173;', 'polyhymnia': '33;', 'ceres': '1;',
             'vesta': '4;', '2015re36': '2015 RE36;'}
_KIAM_LOCK = threading.RLock()  # KIAM changes cwd and uses Fortran module globals.


@lru_cache(maxsize=1)
def native_coverage():
    """Read the installed JPL header; never probe Fortran outside its file."""
    import kiam_astro
    with (Path(kiam_astro.__file__).parent/'JPLEPH').open('rb') as stream:
        stream.seek(3*84+400*6)
        raw=stream.read(24)
    for endian in ('<','>'):
        start,stop,step=struct.unpack(endian+'3d',raw)
        if 1e6<start<stop<4e6 and 0<step<=1024:
            return start,stop
    raise ValueError('Unrecognized KIAM JPLEPH time header')


def canonical(body):
    key = str(body).lower().replace(' ', '').replace('_', '')
    if key not in MAJOR and key not in ASTEROIDS:
        raise ValueError(f'Unknown body {body!r}; register its explicit Horizons ID first')
    return key


def parse_horizons(text):
    if '$$SOE' not in text or '$$EOE' not in text:
        raise ValueError('Horizons did not return a vector table: '+text[-1200:])
    rows = csv.reader(io.StringIO(text.split('$$SOE', 1)[1].split('$$EOE', 1)[0]))
    values = []
    for row in rows:
        if row and row[0].strip():
            values.append([float(row[0]), *[float(x.replace('D', 'E')) for x in row[2:8]]])
    table = np.asarray(values)
    if table.ndim != 2 or table.shape[1] != 7 or len(table) < 1 or not np.isfinite(table).all():
        raise ValueError('Malformed Horizons table')
    if len(table) > 1 and not np.all(np.diff(table[:, 0]) > 0):
        raise ValueError('Horizons epochs are not ordered')
    return table[:, 0], table[:, 1:]*1000


def fetch_vectors(body, *, start=None, stop=None, step='12 h', epochs=None):
    """Explicit download. Retain response and parameters with any cached table."""
    key = canonical(body)
    command = MAJOR[key][1] if key in MAJOR else ASTEROIDS[key]
    params = dict(format='json', COMMAND=f"'{command}'", CENTER="'500@10'",
                  EPHEM_TYPE="'VECTORS'", REF_PLANE="'ECLIPTIC'",
                  REF_SYSTEM="'ICRF'", OUT_UNITS="'KM-S'", VEC_CORR="'NONE'",
                  CSV_FORMAT="'YES'", VEC_TABLE="'2'", TIME_TYPE="'TDB'", OBJ_DATA="'YES'")
    if epochs is not None:
        if not 1 <= len(epochs) <= 10000:
            raise ValueError('Horizons TLIST accepts 1..10000 epochs')
        params['TLIST'] = "'"+'\n'.join(f'{jd:.10f}' for jd in epochs)+"'"
        params['TLIST_TYPE'] = "'JD'"
    else:
        params.update(START_TIME=f"'{start}'", STOP_TIME=f"'{stop}'", STEP_SIZE=f"'{step}'")
    request = urllib.request.Request(API+'?'+urllib.parse.urlencode(params),
                                     headers={'User-Agent': 'trajectory-pipeline/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if 'error' in payload:
        raise ValueError(payload['error'])
    text = payload['result']
    jd, state = parse_horizons(text)
    return jd, state, text, params


def download(body, start, stop, step='12 h', cache=CACHE):
    key = canonical(body)
    folder = Path(cache)/key
    if folder.exists():
        raise FileExistsError(f'{folder} exists; preserve it and choose a new cache root for another interval')
    jd, state, raw, params = fetch_vectors(key, start=start, stop=stop, step=step)
    if len(jd) < 2:
        raise ValueError('Need at least two ephemeris knots')
    folder.mkdir(parents=True)
    (folder/'horizons.txt').write_bytes(raw.encode('utf-8'))
    np.savez_compressed(folder/'vectors.npz', jd_tdb=jd, state_si=state)
    meta = dict(body=key, source=API, parameters=params, center='Sun', frame='ECLIPJ2000',
                time_scale='TDB', units='m,m/s', start_jd=float(jd[0]), stop_jd=float(jd[-1]),
                knots=len(jd), max_step_days=float(np.max(np.diff(jd))),
                interpolation='cubic Hermite, position and velocity from the same polynomial',
                arrays_sha256=sha256(folder/'vectors.npz'), raw_sha256=sha256(folder/'horizons.txt'))
    write_json(folder/'metadata.json', meta)
    return meta


def refine(body, start, stop, step, cache=CACHE):
    """Merge a denser explicitly requested interval, preserving provenance."""
    key = canonical(body)
    folder = Path(cache)/key
    meta = json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    if sha256(folder/'vectors.npz') != meta['arrays_sha256']:
        raise ValueError('Ephemeris checksum mismatch')
    jd, state, raw, params = fetch_vectors(key, start=start, stop=stop, step=step)
    if len(jd) < 2 or jd[0] < meta['start_jd'] or jd[-1] > meta['stop_jd']:
        raise ValueError('Refinement must lie inside existing coverage')
    with np.load(folder/'vectors.npz', allow_pickle=False) as old:
        all_jd = np.r_[jd, old['jd_tdb']]
        all_state = np.vstack([state, old['state_si']])
    merged, indices = np.unique(all_jd, return_index=True)
    number = len(meta.get('refinements', []))+1
    raw_path = folder/f'horizons_refinement_{number}.txt'
    raw_path.write_bytes(raw.encode('utf-8'))
    temporary = folder/'vectors_next.npz'
    np.savez_compressed(temporary, jd_tdb=merged, state_si=all_state[indices])
    meta.setdefault('refinements', []).append(dict(parameters=params, raw=raw_path.name,
                                                  raw_sha256=sha256(raw_path)))
    meta.update(knots=len(merged), arrays_sha256=sha256(temporary),
                max_step_days=float(np.max(np.diff(merged))))
    temporary.replace(folder/'vectors.npz')
    write_json(folder/'metadata.json', meta)
    return meta


class Ephemerides:
    def __init__(self, cache=CACHE):
        self.cache = Path(cache)

    @lru_cache(maxsize=32)
    def _table(self, key):
        folder = self.cache/key
        if not (folder/'metadata.json').exists():
            raise FileNotFoundError(f'No local {key} ephemeris; run the cache command first')
        meta = json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
        if (meta['frame'], meta['center'], meta['time_scale'], meta['units']) != ('ECLIPJ2000', 'Sun', 'TDB', 'm,m/s'):
            raise ValueError('Incompatible ephemeris metadata')
        if sha256(folder/'vectors.npz') != meta['arrays_sha256']:
            raise ValueError('Ephemeris checksum mismatch')
        with np.load(folder/'vectors.npz', allow_pickle=False) as data:
            jd, s = data['jd_tdb'], data['state_si']
        offsets = (jd-jd[0])*DAY_S
        # JD doubles at these epochs resolve only ~40 microseconds. The regular
        # Horizons grids are exact millisecond offsets; eliminate cancellation
        # jitter before differentiating the interpolant, especially at 1-min knots.
        rounded = np.round(offsets, 3)
        if np.max(np.abs(offsets-rounded)) < 0.0002:
            offsets = rounded
        spline = CubicHermiteSpline(offsets, s[:, :3], s[:, 3:], extrapolate=True)
        return jd, spline, meta

    def coverage(self, body):
        key = canonical(body)
        if (self.cache/key/'metadata.json').exists():
            return dict(self._table(key)[2])
        if key in MAJOR:
            start,stop=native_coverage()
            return dict(body=key, start_jd=start, stop_jd=stop,
                        source='KIAM 6.1.6 / bundled JPLEPH', frame='ECLIPJ2000',
                        time_scale='TDB', center='requested', interpolation='KIAM native ephemeris',
                        representation='system barycenter' if key in ('jupiter','saturn','uranus','neptune','pluto') else 'body center')
        return dict(self._table(key)[2])

    def _heliocentric(self, body, epochs):
        key = canonical(body)
        if key == 'sun':
            return np.zeros((len(epochs), 6))
        if (self.cache/key/'metadata.json').exists():
            jd, spline, _ = self._table(key)
            t = (epochs-jd[0])*DAY_S
            return np.c_[spline(t), spline(t, 1)]
        if key in MAJOR:
            from kiam_astro import kiam
            start,stop=native_coverage()
            outside=(epochs<start)|(epochs>stop)
            if np.any(outside):
                state=np.empty((len(epochs),6))
                if np.any(~outside):state[~outside]=self._heliocentric(key,epochs[~outside])
                for mask,knots in ((epochs<start,np.array([start,start+1.])),
                                   (epochs>stop,np.array([stop-1.,stop]))):
                    if not np.any(mask):continue
                    boundary=self._heliocentric(key,knots)
                    extension=CubicHermiteSpline((knots-knots[0])*DAY_S,boundary[:,:3],boundary[:,3:],extrapolate=True)
                    t=(epochs[mask]-knots[0])*DAY_S
                    state[mask]=np.c_[extension(t),extension(t,1)]
                return state
            with _KIAM_LOCK:
                state = np.array([kiam.planet_state(float(jd), 'Sun', MAJOR[key][0]) for jd in epochs])
            # IAU76 J2000 obliquity, the Horizons ECLIPTIC/ICRF convention.
            eps = np.deg2rad(84381.448/3600.)
            rot = np.array([[1, 0, 0], [0, np.cos(eps), np.sin(eps)], [0, -np.sin(eps), np.cos(eps)]])
            return np.c_[state[:, :3]@rot.T, state[:, 3:]@rot.T]*1000
        jd, spline, _ = self._table(key)
        t = (epochs-jd[0])*DAY_S
        return np.c_[spline(t), spline(t, 1)]

    def evaluation_record(self,body,epochs):
        values=np.atleast_1d(np.asarray(epochs,dtype=float))
        if canonical(body)=='sun':return dict(body='sun',extrapolated=False,method='heliocentric origin')
        coverage=self.coverage(body)
        outside=(values<coverage['start_jd'])|(values>coverage['stop_jd'])
        return dict(body=canonical(body),table_start_jd=coverage['start_jd'],table_stop_jd=coverage['stop_jd'],
                    requested_start_jd=float(values.min()),requested_stop_jd=float(values.max()),
                    extrapolated=bool(np.any(outside)),extrapolated_samples=int(outside.sum()),
                    method='endpoint cubic Hermite with derivative velocity' if np.any(outside) else coverage.get('interpolation','source propagation'))

    def state(self, body, jd_tdb, center='Sun'):
        values = np.asarray(jd_tdb, dtype=float)
        if values.ndim > 1 or not np.isfinite(values).all():
            raise ValueError('Expected a finite scalar or vector of JD TDB epochs')
        times = np.atleast_1d(values)
        # Subtracting heliocentric states also supports Earth-centered asteroids.
        result = self._heliocentric(body, times)-self._heliocentric(center, times)
        return result[0] if values.ndim == 0 else result
