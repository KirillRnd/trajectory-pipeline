from pathlib import Path
import json
import numpy as np
from trajectory_pipeline.ephemerides import download,refine,fetch_vectors,Ephemerides,CACHE
from trajectory_pipeline.data import write_json,sha256,DAY_S

root=Path('runs/ephemerides_v4');root.mkdir(exist_ok=True)
bodies=['apophis','eros','bennu','ryugu','polyhymnia','ceres','2015re36','jupiter','saturn','vesta']
for body in bodies:
    folder=root/body
    if not folder.exists():
        print(body,'download 2020–2080',flush=True)
        download(body,'2020-01-01','2080-01-01','12 h',cache=root)
    old=json.loads((CACHE/body/'metadata.json').read_text())
    new=json.loads((folder/'metadata.json').read_text())
    for item in old.get('refinements',[])[len(new.get('refinements',[])):]:
        p=item['parameters']
        refine(body,p['START_TIME'].strip("'"),p['STOP_TIME'].strip("'"),p['STEP_SIZE'].strip("'"),cache=root)
    if (folder/'validation.json').exists():continue
    eph=Ephemerides(root);jd,spline,meta=eph._table(body)
    # Sample uniformly and in the largest changes of acceleration: a finite
    # interpolation audit, explicitly not a bound at every possible epoch.
    with np.load(folder/'vectors.npz') as data:states=data['state_si']
    accel=np.diff(states[:,3:],axis=0)/np.diff(jd)[:,None]/DAY_S
    variation=np.linalg.norm(np.diff(accel,axis=0),axis=1)
    indices=np.unique(np.r_[np.linspace(0,len(jd)-2,96,dtype=int),np.argsort(variation)[-48:]])
    times=(jd[indices]+jd[indices+1])/2
    errors=[]
    for k in range(0,len(times),24):
        epochs,truth,raw,params=fetch_vectors(body,epochs=times[k:k+24])
        (folder/f'validation_{k//24}.txt').write_text(raw)
        actual=eph.state(body,epochs)
        for t,d in zip(epochs,actual-truth):errors.append(dict(jd=float(t),r_m=float(np.linalg.norm(d[:3])),v_m_s=float(np.linalg.norm(d[3:]))))
    write_json(folder/'validation.json',dict(samples=errors,arrays_sha256=sha256(folder/'vectors.npz'),max_position_m=max(e['r_m'] for e in errors),max_velocity_m_s=max(e['v_m_s'] for e in errors)))
    print(body,'validated',max(e['r_m'] for e in errors),max(e['v_m_s'] for e in errors),flush=True)
