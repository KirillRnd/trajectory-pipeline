from pathlib import Path
import json
import numpy as np
from trajectory_pipeline.ephemerides import refine,fetch_vectors,Ephemerides
from trajectory_pipeline.data import write_json,sha256
root=Path('runs/ephemerides_v4')
for folder in sorted(root.iterdir()):
    if not folder.is_dir():continue
    path=folder/'validation.json';record=json.loads(path.read_text())
    for attempt,step in enumerate(['1 h','5 m']):
        bad=sorted(x['jd'] for x in record['samples'] if x['r_m']>100 or x['v_m_s']>.001)
        if not bad:break
        groups=[]
        for t in bad:
            if groups and t-1<=groups[-1][1]:groups[-1][1]=t+1
            else:groups.append([t-1,t+1])
        if attempt==0 and len(bad)>len(record['samples'])/10:
            meta=json.loads((folder/'metadata.json').read_text())
            groups=[[meta['start_jd'],meta['stop_jd']]];step='6 h'
        for start,stop in groups:
            print(folder.name,'refine',start,stop,step,flush=True)
            refine(folder.name,f'JD{start}',f'JD{stop}',step,cache=root)
        eph=Ephemerides(root);errors=[]
        times=[x['jd'] for x in record['samples']]
        # Validate the original probes and midpoints of each new refined span.
        for start,stop in groups:times.extend(np.linspace(start+.001,stop-.001,32).tolist())
        times=sorted(set(times))
        for k in range(0,len(times),24):
            epochs,truth,raw,params=fetch_vectors(folder.name,epochs=times[k:k+24])
            (folder/f'validation_refined_{attempt}_{k//24}.txt').write_text(raw)
            for t,d in zip(epochs,eph.state(folder.name,epochs)-truth):errors.append(dict(jd=float(t),r_m=float(np.linalg.norm(d[:3])),v_m_s=float(np.linalg.norm(d[3:]))))
        path.replace(folder/f'validation_before_refine_{attempt}.json')
        record=dict(samples=errors,arrays_sha256=sha256(folder/'vectors.npz'),max_position_m=max(e['r_m'] for e in errors),max_velocity_m_s=max(e['v_m_s'] for e in errors))
        write_json(path,record)
    assert record['max_position_m']<=100 and record['max_velocity_m_s']<=.001,(folder.name,record['max_position_m'],record['max_velocity_m_s'])
    print(folder.name,'accepted interpolation probes',record['max_position_m'],record['max_velocity_m_s'],flush=True)
