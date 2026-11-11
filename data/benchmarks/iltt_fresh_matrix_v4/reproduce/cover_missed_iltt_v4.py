"""Uniform second pass: at most two viable date/branch inputs missed by GA.

No per-body numerical tuning; every pair tries the same two engines/routes.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json,subprocess,sys,time,os,signal
from trajectory_pipeline.data import write_json,sha256
from trajectory_pipeline.runtime import runtime_environment

first=Path('runs/iltt_fresh_matrix_v4_full');root=Path('runs/iltt_missed_inputs_v4')
root.mkdir(exist_ok=True);(root/'inputs').mkdir(exist_ok=True);(root/'logs').mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
bases={r['case_id']:r for r in read(first/'matrix.json')}
preflight=read(Path('runs/iltt_preflight_v4/results.json'))
design=read(first/'design.json');plans=read(root/'plan.json') if (root/'plan.json').exists() else {};results={};handled=set();jobs={}
for summary_path in root.glob('*/summary.json'):
    name=summary_path.parent.name;mission=read(root/'inputs'/f'{name}.json')
    results[name]=dict(read(summary_path),case_id=mission['case_id'],name=name)
write_json(root/'results.json',list(results.values()))
if not (root/'protocol.json').exists():
    write_json(root/'protocol.json',dict(version=2,max_inputs_per_case=2,selection='Resolved and covered date/branch inputs with unvisited hardware; at most two pairs per case; order abs(date offset), derived duration, branch',engines=design['engines'],population=2,generations=1,wall_budget_s=1800,history=[],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),environment=runtime_environment(),preflight_sha256=sha256(Path('runs/iltt_preflight_v4/results.json'))))
def run(name,mission,local):
    write_json(root/'inputs'/f'{name}.json',mission);write_json(root/'inputs'/f'{name}_design.json',local)
    print(name,'started',flush=True);started=time.perf_counter()
    with (root/'logs'/f'{name}.log').open('w') as log:
        p=subprocess.Popen([sys.executable,'-m','trajectory_pipeline','search',str(root/'inputs'/f'{name}.json'),'--design',str(root/'inputs'/f'{name}_design.json'),'--output',str(root/name)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:p.wait(timeout=1900)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    summary=read(root/name/'summary.json') if (root/name/'summary.json').exists() else dict(status='controller_failed',accepted=0)
    print(name,summary['status'],'accepted',summary.get('accepted'),flush=True)
    return dict(summary,case_id=mission['case_id'],name=name,controller_elapsed_s=time.perf_counter()-started)
with ThreadPoolExecutor(max_workers=4) as pool:
    deadline=time.perf_counter()+10000
    while len(handled)<len(bases) or jobs:
        if time.perf_counter()>deadline:raise TimeoutError('Supplementary controller wait limit')
        completed=read(first/'results.json') if (first/'results.json').exists() else []
        for case in completed:
            name=case['case_id']
            if name in handled:continue
            handled.add(name)
            if case.get('accepted',0):plans[name]=dict(reason='physical solution already found');continue
            graph=read(first/name/'graph.json');visited={}
            nodes=list(graph['nodes'].values())
            for previous in results.values():
                if previous['case_id']==name:nodes.extend(read(root/previous['name']/'graph.json')['nodes'].values())
            for node in nodes:
                if node['request']['operation']!='cold':continue
                m=node['request']['mission']
                offset=round((datetime.fromisoformat(m['launch_tdb'])-datetime.fromisoformat(bases[name]['launch_tdb'])).total_seconds()/86400)
                engine=(m['spacecraft']['thrust_N'],m['spacecraft']['exhaust_velocity_m_s'])
                visited.setdefault((offset,m['solver']['iltt_branch']),set()).add(engine)
            viable=[]
            for r in preflight:
                if r['case_id']!=name or r['status']!='resolved' or not r['time_interval_covered']:continue
                missing=[e for e in design['engines'] if (e['thrust_N'],e['exhaust_velocity_m_s']) not in visited.get((r['offset_days'],r['branch']),set())]
                if missing:viable.append(dict(r,missing_engines=missing))
            viable.sort(key=lambda r:(abs(r['offset_days']),r['iltt']['tof_days'],r['branch']))
            previous_selected=plans.get(name,{}).get('selected',[])
            selected=viable[:max(0,2-len(previous_selected))]
            plans[name]=dict(visited=[dict(offset=k[0],branch=k[1],engines=sorted(v)) for k,v in sorted(visited.items())],unvisited_viable=len(viable),selected=previous_selected+selected)
            for i,r in enumerate(selected):
                local=dict(design,date_offsets_days=[r['offset_days']],angular_branches=[r['branch']],engines=r['missing_engines'],population=len(r['missing_engines']),generations=1,wall_budget_s=1800)
                key=f'{name}_input_{len(previous_selected)+i+1}';jobs[pool.submit(run,key,bases[name],local)]=key
        write_json(root/'plan.json',plans)
        for future in list(jobs):
            if future.done():
                key=jobs.pop(future);results[key]=future.result();write_json(root/'results.json',list(results.values()))
        if len(handled)<len(bases) or jobs:time.sleep(5)
write_json(root/'summary.json',dict(status='finished',cases_considered=len(handled),searches=len(results),found_cases=sorted({r['case_id'] for r in results.values() if r.get('accepted',0)})))
