import json,traceback
from pathlib import Path
import numpy as np
import trajectory_pipeline.free_time as ft
from trajectory_pipeline.date_sweep import _fast_worker
from trajectory_pipeline.data import write_json
root=Path('runs/apophis_daily_routes_v1/chains/2028-02-23/r_free')
out=root/'diagnostic_assembly';out.mkdir(exist_ok=False)
original_assemble=ft.assemble
def assembly(source,model,times,states,*args,**kwargs):
    p=out/f'assembly_{len(list(out.glob("assembly_*")))}';p.mkdir()
    np.savez_compressed(p/'assembly.npz',times=times,states=states,throttle=kwargs['throttle_override'])
    write_json(p/'clock.json',dict(scales=source.metadata['scales'],mission=source.metadata['mission'],switch_times_s=kwargs['extra']['switch_times_s'],last_times=times[-3:].tolist(),last_mass=states[6,-3:].tolist()))
    return original_assemble(source,model,times,states,*args,**kwargs)
ft.assemble=assembly
original=ft.verify_bounded
def capture(result,*args,**kwargs):
    check=original(result,*args,**kwargs)
    if not check['passed']:
        p=out/f'candidate_{len(list(out.glob("candidate_*")))}';result.save(p)
        a=result.arrays;m=result.metadata;mission=m['mission']
        durations=np.diff(np.r_[0,m['switch_times_s'],mission['tof_days']*86400])
        flags=np.where(np.arange(len(durations))%2==0,m['initial_throttle'],1-m['initial_throttle'])
        used=mission['spacecraft']['thrust_N']/mission['spacecraft']['exhaust_velocity_m_s']*(durations@flags)
        write_json(p/'diagnostic.json',dict(check=check,used_kg=float(used),mass_loss_kg=float(a['mass_kg'][0]-a['mass_kg'][-1]),last_times=a['t_s'][-3:].tolist(),last_masses=a['mass_kg'][-3:].tolist(),duration_s=mission['tof_days']*86400))
    return check
ft.verify_bounded=capture
try:_fast_worker(root/'sweep.json',root/'mission.json',out)
except Exception as exc:write_json(out/'error.json',dict(error=str(exc)))
for p in out.glob('candidate_*/diagnostic.json'):print(p.read_text())
