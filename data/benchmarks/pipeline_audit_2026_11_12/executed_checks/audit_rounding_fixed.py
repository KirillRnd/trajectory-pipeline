from pathlib import Path
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.orbital_pipeline import run_orbital_pipeline
m=Mission.load('runs/audit_orbital_time_v2/mars_spiral_impulse_dry60/time_trial_000/mission.json')
r,s=run_orbital_pipeline(m,'runs/audit_rounding_fixed')
print(s['status'],s.get('error'),flush=True)