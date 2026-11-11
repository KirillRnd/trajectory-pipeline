from pathlib import Path
import json,shutil
from trajectory_pipeline.data import sha256,write_json
source=Path('runs/search_matrix_v1'); destination=Path('runs/search_matrix_v1_archive')
rows=json.loads((source/'verified_results.json').read_text())
assert len(rows)==15 and all(r['summary']['status'] in ('finished','budget_exhausted') for r in rows)
assert len(json.loads((source/'results.json').read_text()))==15
destination.mkdir(exist_ok=False)
files={p for p in source.rglob('*') if p.is_file() and p.suffix in ('.json','.log','.md','.csv') and 'plots' not in p.parts}
files.update(source.glob('*/nodes/*/final/trajectory.npz'))
files.update(source.glob('*/nodes/*/run/final/trajectory.npz'))
for checkpoint in source.rglob('continuation.json'):
    state=json.loads(checkpoint.read_text())
    if state.get('last_point'):
        array=checkpoint.parent/state['last_point']/'trajectory.npz'
        if array.exists():files.add(array)
manifest=[]
for p in sorted(files):
    relative=p.relative_to(source);out=destination/relative;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
    checksum=sha256(p);assert checksum==sha256(out)
    manifest.append(dict(path=relative.as_posix(),sha256=checksum,bytes=p.stat().st_size))
for name in ('run_search_matrix_v1.py','report_search_matrix_v1.py','archive_search_matrix_v1.py'):
    p=Path('runs')/name;out=destination/'reproduction'/name;out.parent.mkdir(exist_ok=True);shutil.copy2(p,out)
    manifest.append(dict(path=out.relative_to(destination).as_posix(),sha256=sha256(out),bytes=out.stat().st_size))
# Audit portable accepted arrays once more against hashes; all original paths retained as provenance.
for row in rows:
    for result in row['accepted']:
        g=json.loads((destination/row['case_id']/'graph.json').read_text());n=g['nodes'][result['node']]
        p=destination/row['case_id']/'nodes'/result['node']/'final'
        assert sha256(p/'trajectory.json')==n['metadata_sha256']
        assert sha256(p/'trajectory.npz')==n['arrays_sha256']
write_json(destination/'manifest.json',dict(files=manifest,scope='All graph metadata, inputs, histories and logs; accepted final and last continuation arrays. Full intermediate arrays and figures remain under runs/search_matrix_v1. Original paths in provenance are not rewritten.'))
print(len(manifest),'files;',sum(f['bytes'] for f in manifest),'bytes; accepted copies verified')
