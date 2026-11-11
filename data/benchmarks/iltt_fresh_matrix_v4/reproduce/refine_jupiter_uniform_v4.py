from pathlib import Path
import json
import numpy as np
from trajectory_pipeline.ephemerides import refine,fetch_vectors,Ephemerides
from trajectory_pipeline.data import write_json,sha256
root=Path('runs/ephemerides_v4');folder=root/'jupiter'
for start,stop in [('2020-01-01','2050-01-01'),('2050-01-01','2080-01-01')]:
    print('Jupiter uniform 3h',start,stop,flush=True)
    refine('jupiter',start,stop,'3 h',cache=root)
old=json.loads((folder/'validation.json').read_text());eph=Ephemerides(root)
times=sorted(set([x['jd'] for x in old['samples']]+np.linspace(2458849.51,2480764.49,192).tolist()))
errors=[]
for k in range(0,len(times),24):
    epochs,truth,raw,_=fetch_vectors('jupiter',epochs=times[k:k+24])
    (folder/f'validation_uniform3h_{k//24}.txt').write_text(raw)
    for t,d in zip(epochs,eph.state('jupiter',epochs)-truth):errors.append(dict(jd=float(t),r_m=float(np.linalg.norm(d[:3])),v_m_s=float(np.linalg.norm(d[3:]))))
(folder/'validation.json').replace(folder/'validation_before_uniform3h.json')
record=dict(samples=errors,arrays_sha256=sha256(folder/'vectors.npz'),max_position_m=max(e['r_m'] for e in errors),max_velocity_m_s=max(e['v_m_s'] for e in errors))
write_json(folder/'validation.json',record)
print({k:v for k,v in record.items() if k!='samples'},flush=True)
assert record['max_position_m']<100 and record['max_velocity_m_s']<.001
