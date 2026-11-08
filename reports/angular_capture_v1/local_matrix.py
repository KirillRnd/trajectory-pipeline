import json,time,numpy as np
import argparse
from pathlib import Path
parser=argparse.ArgumentParser(description='Independent physical angular capture matrix; run in Docker')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists(): raise FileExistsError(args.output)
args.output.parent.mkdir(parents=True,exist_ok=True)
from trajectory_pipeline.planetary_capture import *
from trajectory_pipeline.capture_control import capture_budget_check
cases=[
 ('mars',4.2828375662e13,3396190.,400e3,30000e3,577230383.942,90.,.025,20000.,{'mode':'angular','half_width_rad':2.}),
 ('mars_engine',4.2828375662e13,3396190.,400e3,30000e3,577230383.942,60.,.04,16000.,{'mode':'angular','half_width_rad':2.7}),
 ('venus',3.24859e14,6051800.,400e3,30000e3,616e6,80.,.04,22000.,{'mode':'angular','half_width_rad':2.}),
 ('earth',3.986004356e14,6378137.,400e3,30000e3,924881552.,110.,.06,25000.,{'mode':'angular','half_width_rad':2.4}),
 ('ceres',6.26325e10,469700.,100e3,3000e3,75e6,60.,.002,16000.,{'mode':'angular','half_width_rad':2.}),
 ('mars_fixed',4.2828375662e13,3396190.,400e3,30000e3,577230383.942,90.,.025,20000.,{'mode':'angular','phase_reference':'fixed_axis','half_width_rad':2.4}),
 ('mars_affine',4.2828375662e13,3396190.,400e3,30000e3,577230383.942,90.,.025,20000.,{'mode':'angular','half_width_rad':1.8,'eccentricity_slope_rad':.25}),
]
rows=[]
for name,mu,R,hp,ha,join,m,F,c,control in cases:
 t=time.time();row=dict(case=name,mu=mu,planet_radius_m=R,periapsis_altitude_m=hp,apoapsis_altitude_m=ha,interface_radius_m=join,final_mass_kg=m,thrust_N=F,exhaust_velocity_m_s=c,control=control)
 try:
  orbit=CaptureOrbit(mu,R,hp,ha,join);b=backward_capture(orbit,m,F,c,control=control)
  f=forward_capture(orbit,b['relative_state_si'][0],b['entry_mass_kg'],F,c,b['burn_start_s'],b['duration_s'],control=b['control'],reference_axis=b['reference_axis'],sample_times=b['t_s'])
  i=np.searchsorted(f['t_s'],b['t_s']);dr=float(np.linalg.norm(f['relative_state_si'][i,:3]-b['relative_state_si'][:,:3],axis=1).max());dv=float(np.linalg.norm(f['relative_state_si'][i,3:]-b['relative_state_si'][:,3:],axis=1).max());dm=abs(float(f['mass_kg'][-1])-m)
  flow=abs(b['entry_mass_kg']-m-F/c*b['active_duration_s']);events=len(f['arcs'])==len(b['arcs']);dt=max(abs(x['end_s']-y['end_s']) for x,y in zip(f['arcs'],b['arcs'])) if events else None
  row.update(status='passed' if dr<100 and dv<.01 and dm<1e-6 and flow<1e-6 and events and dt<.05 else 'failed_replay',duration_days=b['duration_s']/86400,active_days=b['active_duration_s']/86400,propellant_kg=b['entry_mass_kg']-m,position_error_m=dr,velocity_error_m_s=dv,mass_error_kg=dm,mass_flow_error_kg=flow,event_time_error_s=dt,arcs=len(b['arcs']))
 except (ValueError,RuntimeError) as e:row.update(status='failed',error=str(e))
 row['wall_s']=time.time()-t;rows.append(row);print(json.dumps(row),flush=True)
 args.output.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
