from pathlib import Path
import shutil,json,sys
from trajectory_pipeline.data import sha256,write_json

prepared='--prepared' in sys.argv
root=Path('runs/archive_iltt_fresh_v4');root.mkdir(exist_ok=prepared)
sources=['iltt_fresh_matrix_v4_full','iltt_missed_inputs_v4','iltt_preflight_v4','iltt_standard_jan2029_v4','iltt_sweep_fallback_v4_checked','iltt_dispatch_checked_v4']
allowed={'.json','.npz','.log','.csv','.txt','.md'}
for name in ([] if prepared else sources):
    source=Path('runs')/name
    for p in source.rglob('*'):
        if p.is_file() and p.suffix in allowed and 'plots' not in p.parts:
            destination=root/'snapshot'/p;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,destination)
scripts=['run_fresh_iltt_matrix_v4.py','preflight_iltt_v4.py','preflight_iltt_bounded_v4.py','cover_missed_iltt_v4.py',
         'report_fresh_iltt_matrix_v4.py','report_preflight_v4.py','expand_ephemerides_v4.py','refine_ephemerides_v4.py',
         'refine_jupiter_uniform_v4.py','report_ephemerides_v4.py','archive_iltt_fresh_v4.py','render_fresh_iltt_v4.py']
(root/'reproduce').mkdir()
for name in scripts:shutil.copy2(Path('runs')/name,root/'reproduce'/name)
for variant in ['reporting_dispatch_v4','reporting_dispatch_v4b']:
    destination=root/'reproduce'/variant;destination.mkdir()
    for p in (Path('runs')/variant).glob('*.py'):shutil.copy2(p,destination/p.name)
shutil.copy2('runs/ephemerides_v4_audit.json',root/'ephemerides_audit.json')
plots=Path('output/pipeline/iltt_fresh_matrix_v4')
for p in plots.rglob('*.jpg'):
    destination=root/'figures'/p.relative_to(plots);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,destination)
(root/'README.md').write_text('''# Fresh date-first ILTT audit

Source for the numerical matrix: e113b305 (module hashes and Docker image ID
are saved per search). All 15 original cases have tof_days=null on input.
Historical physical references are absent. The Moon is excluded.

`snapshot/runs/` preserves original relative paths, intermediate arrays,
requests, graph edges, continuation histories and checks. Derived plot files
are omitted; they can be rendered from the saved arrays. No numerical endpoint
is replaced by a plot or a controller success flag.

The primary and supplementary studies are separate. The latter only covers
up to two viable, unvisited date/branch inputs per case without an accepted
primary solution; its protocol and selection are saved explicitly.

The January Mars standard-solve control is additional to the 15 cases. The
sweep control intentionally gives the fast route a tiny budget to exercise
standard fallback; its partial physical outcome is not a successful solution.

For read-only replay, load any saved trajectory.json/trajectory.npz pair with
Trajectory.load and the corresponding independent verifier in Linux Docker.
To reuse original graph paths in a clean clone, copy snapshot/runs/* into the
empty repository runs/ directory before running the report. Do not overwrite
an existing study. To recalculate instead, use reproduce/run_fresh_iltt_matrix_v4.py
with a new output directory; the script refuses an existing output directory.

The optional download/refinement scripts describe preparation of the frozen
2020–2080 ephemerides. The actual verified tables and raw Horizons responses
are versioned in data/ephemerides; no network is needed to run the matrix.
Interpolation probes are not a bound on orbital prediction uncertainty.
''')
files=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha256(p)) for p in sorted(root.rglob('*')) if p.is_file()]
write_json(root/'manifest.json',dict(files=files,total_bytes=sum(r['bytes'] for r in files)))
print('Archived',len(files),'files;',sum(r['bytes'] for r in files),'bytes')
