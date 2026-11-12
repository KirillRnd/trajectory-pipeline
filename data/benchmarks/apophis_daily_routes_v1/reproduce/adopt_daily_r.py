import os,signal,json,time
from pathlib import Path
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.contract import audit_configuration

folder=Path('runs/apophis_daily_routes_v1/chains/2028-02-23')
request=json.loads((folder/'request.json').read_text());wanted=Mission(**request['mission'])
results={}
for kind in ('fixed','free'):
    out=folder/('r_'+kind)
    row=json.loads((out/'fast'/wanted.case_id/'result.json').read_text())
    if row['status']=='completed':
        artifact=out/row['attempt']/'final';t=Trajectory.load(artifact)
        actual=Mission(**t.metadata['mission']);audit_configuration(t,replace(wanted,tof_days=actual.tof_days),require_final=True)
        assert request['bounds_days'][0]<=actual.tof_days<=request['bounds_days'][1]
        assert t.metadata['verification']['passed'] and t.metadata['kiam_verification']['passed']
        results[kind]=(t,row)
assert 'fixed' in results
# Stop only the exact cold-route child after an independent physical route has
# passed. Its accepted checkpoints remain untouched; other jobs are unaffected.
stopped=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
    try:args=(proc/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,PermissionError,ProcessLookupError):continue
    if len(args)>=5 and args[1].endswith(b'/apophis_daily_routes.py') and args[2]==b'chain' and args[4].decode()==str(folder):
        os.kill(int(proc.name),signal.SIGSTOP);stopped.append(int(proc.name))
old=json.loads((folder/'summary.json').read_text());write_json(folder/'cold_route_stopped.json',dict(reason='Independent R route accepted; no need to finish slower cold continuation',pids=stopped,last_summary=old))
old['stages'].append(dict(route_stage='R_transfer',status='completed',reference='2028-02-25',duration_changed=True,hardware_changed=False))
if 'free' not in results:
    failed=json.loads((folder/'r_free/fast'/wanted.case_id/'result.json').read_text())
    old['stages'].append(dict(route_stage='R_free_time',status='partial',error=failed.get('error')))
for kind,name in [('fixed','physical'),('free','free_time')]:
    if kind not in results:continue
    t,row=results[kind];t.save(folder/name)
    old[name]=dict(path=str(folder/name),tof_days=t.metadata['mission']['tof_days'],fuel_kg=float(t.arrays['mass_kg'][0]-t.arrays['mass_kg'][-1]),verification=t.metadata['verification'],kiam=t.metadata['kiam_verification'])
old.update(status='completed' if old.get('free_time') else 'physical_fixed_time',phase='R_transfer',selected_route='nearest_original_anchor_R_transfer')
old.pop('error',None);write_json(folder/'summary.json',old)
for pid in stopped:
    os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT)
print(old['status'],{k:v[1].get('fuel_kg') for k,v in results.items()},'stopped cold',stopped)
