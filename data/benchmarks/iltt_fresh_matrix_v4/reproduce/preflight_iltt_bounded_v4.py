from pathlib import Path
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,subprocess,sys
from trajectory_pipeline.problem import Mission
from trajectory_pipeline.iltt_entry import angular_branches,resolve_date_mission
from trajectory_pipeline.ephemerides import Ephemerides
from trajectory_pipeline.data import write_json

root=Path('runs/iltt_preflight_v4')
def evaluate(raw):
    row=dict(case_id=raw['case_id'],offset_days=raw.pop('_offset'),branch=raw['solver']['iltt_branch'])
    try:
        eph=Ephemerides();m=Mission(**raw).validate()
        _,_,_,_,_,phase,branches=angular_branches(m,eph)
        row.update(phase_rad=phase,branches=branches)
        m=resolve_date_mission(m,eph);row.update(status='resolved',iltt=m.solver['iltt_resolved'])
        row['time_interval_covered']=all(m.launch_jd>=eph.coverage(b)['start_jd'] and m.launch_jd+m.tof_days*1.5<=eph.coverage(b)['stop_jd'] for b in (m.departure,m.target))
    except Exception as exc:row.update(status='failed',error=type(exc).__name__+': '+str(exc))
    return row

if len(sys.argv)>1:
    write_json(Path(sys.argv[2]),evaluate(json.loads(sys.argv[1])))
else:
    root.mkdir(exist_ok=True);(root/'attempts').mkdir(exist_ok=True)
    bases=json.loads(Path('data/benchmarks/search_matrix_v1/matrix.json').read_text())
    design=json.loads(Path('configs/search_graph_fresh_iltt_v4.json').read_text())
    rows=json.loads((root/'results.json').read_text()) if (root/'results.json').exists() else []
    done={(r['case_id'],r['offset_days'],r['branch']) for r in rows};tasks=[]
    for base in bases:
        for offset in design['date_offsets_days']:
            for branch in design['angular_branches']:
                if (base['case_id'],offset,branch) in done:continue
                tasks.append(dict(base,_offset=offset,tof_days=None,launch_tdb=(datetime.fromisoformat(base['launch_tdb'])+timedelta(days=offset)).isoformat(),solver=dict(base['solver'],irt_entry='date',iltt_branch=branch)))
    def execute(raw):
        p=root/'attempts'/f"{raw['case_id']}_{raw['_offset']}_{raw['solver']['iltt_branch']}.json"
        try:
            with p.with_suffix('.log').open('w') as log:
                subprocess.run([sys.executable,__file__,json.dumps(raw),str(p)],stdout=log,stderr=subprocess.STDOUT,timeout=40,check=True)
            return json.loads(p.read_text())
        except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
            row=dict(case_id=raw['case_id'],offset_days=raw['_offset'],branch=raw['solver']['iltt_branch'],status='failed',error=type(exc).__name__+': bounded ILTT preflight')
            write_json(p,row);return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(execute,r) for r in tasks]):
            row=future.result();rows.append(row);write_json(root/'results.json',rows)
            print(row['case_id'],row['offset_days'],row['branch'],row['status'],flush=True)
    eph=Ephemerides()
    write_json(root/'coverage.json',{b:eph.coverage(b) for b in sorted({r[k] for r in bases for k in ('departure','target')})})
    assert len(rows)==210
