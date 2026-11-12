import json
from concurrent.futures import ThreadPoolExecutor
from apophis_daily_routes import ROOT,worker
from trajectory_pipeline.data import write_json
anchors=json.loads((ROOT/'design.json').read_text())['anchors']
with ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(worker,[r['artifact'] for r in anchors]))
write_json(ROOT/'anchor_recovery.json',rows)
