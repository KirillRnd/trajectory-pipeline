import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from trajectory_pipeline.coordinate_matrix import worker
from trajectory_pipeline.data import write_json

if __name__=='__main__':
    source=Path('runs/coordinate_matrix_v1');root=Path('runs/coordinate_matrix_branch1_v1');root.mkdir(exist_ok=False)
    configs={m['case_id']:m for m in json.loads((source/'design.json').read_text())['requests']}
    failed=[r for r in json.loads((source/'results.json').read_text()) if not r['accepted']]
    requests=[]
    for row in failed:
        m=configs[row['case_id']];m['case_id']+='_branch1';m['solver']['iltt_branch']=1
        requests.append((m,str(root/m['case_id'])))
    write_json(root/'design.json',dict(parent=str(source),rule='All failed rows, next positive date-derived branch; same dates and budgets',requests=[r[0] for r in requests]))
    rows=[]
    with ProcessPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(worker,r) for r in requests]):
            row=future.result();rows.append(row);write_json(root/'results.json',rows)
            print(row['case_id'],row['accepted'],flush=True)
