from pathlib import Path
import json,shutil
from trajectory_pipeline.data import sha256,write_json,Trajectory
from trajectory_pipeline.search_graph import check_result
from trajectory_pipeline.problem import Mission
sources={'standard':Path('runs/search_intermediate_matrix_v2'),'extended':Path('runs/search_intermediate_long_v2')}
for source in sources.values():
    assert len(json.loads((source/'verified_results.json').read_text()))==5
    assert len(json.loads((source/'results.json').read_text()))==5
dest=Path('runs/intermediate_time_v2_archive');dest.mkdir(exist_ok=False);manifest=[]
def register(p):manifest.append(dict(path=p.relative_to(dest).as_posix(),sha256=sha256(p),bytes=p.stat().st_size))
def copy_tree(src,prefix):
    files={p for p in src.rglob('*') if p.is_file() and p.suffix in ('.json','.log','.md','.csv') and 'plots' not in p.parts}
    for pattern in ('*/nodes/*/final/trajectory.npz','*/nodes/*/intermediate/trajectory.npz','*/nodes/*/run/final/trajectory.npz',
                    '*/final/trajectory.npz','*/intermediate/trajectory.npz','last/trajectory.npz','bridge/trajectory.npz','*/parent/trajectory.npz'):
        files.update(src.glob(pattern))
    for cp in src.rglob('continuation.json'):
        state=json.loads(cp.read_text())
        if state.get('last_point'):
            p=cp.parent/state['last_point']/'trajectory.npz'
            if p.exists():files.add(p)
    for p in sorted(files):
        out=dest/prefix/p.relative_to(src);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
        assert sha256(p)==sha256(out);register(out)
for label,source in sources.items():
    copy_tree(source,Path(label))
    for row in json.loads((source/'verified_results.json').read_text()):
        graph=json.loads((dest/label/row['case_id']/'graph.json').read_text())
        for nid,n in graph['nodes'].items():
            if n.get('artifact'):
                folder=dest/label/row['case_id']/'nodes'/nid/Path(n['artifact']).name
                assert sha256(folder/'trajectory.json')==n['metadata_sha256']
                assert sha256(folder/'trajectory.npz')==n['arrays_sha256']
copy_tree(Path('runs/intermediate_time_budget_control'),Path('budget_control'))
for label,source,final in [('time','runs/intermediate_time_positive_mars2028','physical_continue/final'),
                           ('joint','runs/intermediate_time_joint_control','last')]:
    copy_tree(Path(source),Path('controls')/label)
    result=Trajectory.load(dest/'controls'/label/final)
    check,kiam=check_result(result,Mission(**result.metadata['mission']))
    p=dest/'controls'/label/'recheck.json';write_json(p,dict(verification=check,kiam_verification=kiam,mission=result.metadata['mission']));register(p)
for name in ('run_search_intermediate_matrix_v2.py','run_search_intermediate_long_v2.py','report_search_intermediate_matrix_v2.py',
             'archive_search_intermediate_matrix_v2.py','intermediate_time_budget_control.py','verify_intermediate_time_budget_control.py','intermediate_time_positive_mars2028.py','intermediate_time_joint_control.py'):
    p=Path('runs')/name;out=dest/'reproduction'/name;out.parent.mkdir(exist_ok=True);shutil.copy2(p,out);register(out)
p=dest/'README.md'
p.write_text('''# Intermediate-time search validation

`standard/`: all five previous failures, 4 individuals x 2 generations, time upper 1.5T.
`extended/`: additional uniform probe, both engines at 1.2T seed and upper 2T, unchanged original launch dates.
`controls/time/`: real Mars-2028 intermediate duration release followed by independently accepted physical PSI.
`controls/joint/`: real Mars-2028 verified bridge with beta=0.7 and force 1.2 times hardware, followed by joint mass/force continuation and exact physical PSI.

Standard/extended numerical implementation: commit 69460613. Budget control: commit 50281651; all five remain partial at mass_and_thrust after uniform 180-second continuation budgets. Parent selection minimizes abs(log(force ratio)) + 1-beta; only solver budgets change. Inputs, design, image ID, code hashes and original provenance paths are retained.
Every graph artifact is included. Unselected duration trial arrays, earlier continuation arrays and plots remain in original runs.
Original paths inside JSON are provenance, not relocated links. Load archived trajectories from their actual archive folders.
For graph-aware history ingestion, pass an individual case folder containing graph.json, not this collection root.
Intermediate checkpoints are available to the Python API; graph history currently imports physical PSI references only.
''');register(p)
write_json(dest/'manifest.json',dict(files=manifest,scope='All metadata/logs; every declared graph artifact, last continuation arrays, two real Mars controls. Earlier/unselected arrays remain under runs. Provenance paths preserved.'))
print(len(manifest),'files;',sum(p['bytes'] for p in manifest),'bytes; graph and control artifact hashes checked')

