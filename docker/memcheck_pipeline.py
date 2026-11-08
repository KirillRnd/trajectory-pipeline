"""Instrument one complete solve, not an acceptance sweep or a new solver.

Run inside the diagnostic image. Scale only the monotonic budget clock before
importing solver modules, preserving mission JSON and dimensional flight time.
The actual instruction path can still differ under Valgrind; this does not
claim instruction-for-instruction reproduction of the failing process.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time


parser=argparse.ArgumentParser()
parser.add_argument('mission')
parser.add_argument('--output',required=True)
parser.add_argument('--clock-scale',type=float,default=20.)
args=parser.parse_args()
import math
if not math.isfinite(args.clock_scale) or args.clock_scale<=0:parser.error('Clock scale must be finite and positive')
output=Path(args.output)
if output.exists():parser.error('Use a new diagnostic output directory')
output.parent.mkdir(parents=True,exist_ok=True)
if (output.parent/'diagnostic_run.json').exists():parser.error('Diagnostic parent already has a manifest')
mission=Path(args.mission)
real_counter=time.perf_counter
started=real_counter()
manifest=dict(diagnostic_only=True,input_file=str(mission),input_sha256=hashlib.sha256(mission.read_bytes()).hexdigest(),
              mission=json.loads(mission.read_text(encoding='utf-8')),clock_scale=args.clock_scale,
              physical_flight_time_scaled=False,solver_files_modified=False,
              interpretation='Budget clock only; full numerical history may differ under instrumentation')
(output.parent/'diagnostic_run.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
time.perf_counter=lambda:started+(real_counter()-started)/args.clock_scale

from trajectory_pipeline.data import Trajectory
original_save=Trajectory.save
def diagnostic_save(self,*values,**keywords):
    self.metadata['diagnostic_only']=True
    self.metadata['diagnostic_clock_scale']=args.clock_scale
    return original_save(self,*values,**keywords)
Trajectory.save=diagnostic_save
sys.argv=['trajectory_pipeline','solve',str(mission),'--output',str(output)]
print('Full diagnostic solve; unchanged mission JSON; scaled budget clock; not an acceptance run',flush=True)
try:
    runpy.run_module('trajectory_pipeline',run_name='__main__')
finally:
    manifest['actual_wall_elapsed_s']=real_counter()-started
    manifest['solver_files_modified']=False
    (output.parent/'diagnostic_run.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
