from pathlib import Path
import hashlib, json, os, re, subprocess, sys, tempfile
workspace=Path('/workspace')
manifest=json.loads((workspace/'migration_manifest.json').read_text())
revision=manifest['imported_git_revision']
with tempfile.TemporaryDirectory(prefix='trajectory-checkout-') as folder:
    checkout=Path(folder)
    archive=subprocess.Popen(['git','archive',revision],cwd=workspace,stdout=subprocess.PIPE)
    extracted=subprocess.run(['tar','-xf','-','-C',folder],stdin=archive.stdout,check=True)
    archive.stdout.close()
    assert archive.wait()==0
    mismatches=[]
    for row in manifest['files']:
        path=checkout/row['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            mismatches.append(row['path'])
    assert not mismatches,mismatches
    os.chdir(checkout)
    sys.path.insert(0,str(checkout))
    from trajectory_pipeline.data import Trajectory
    from trajectory_pipeline.orbital_pipeline import verify_orbital_mission
    from trajectory_pipeline.ummp import verify_ummp
    import trajectory_pipeline.data as data_module
    assert Path(data_module.__file__).is_relative_to(checkout)
    arrays=0
    for path in (checkout/'data').rglob('trajectory.json'):
        meta=json.loads(path.read_text())
        assert hashlib.sha256(path.with_name('trajectory.npz').read_bytes()).hexdigest()==meta['arrays_sha256'],str(path)
        arrays+=1
    checks={}
    for dep in ('impulse','spiral'):
        for arr in ('impulse','spiral'):
            case=f'mars_{dep}_{arr}_dry60'
            result=verify_orbital_mission(checkout/'data/benchmarks/orbital_modes_v1/dry60'/case)
            assert result['passed'],case
            checks[case]=result
    ummp=verify_ummp(Trajectory.load(checkout/'data/benchmarks/ummp_apophis_156kg_benchmark/ummp/point_0004'))
    assert ummp['passed']
    with (workspace/'runs/extraction-clean-help.log').open('w') as out:
        subprocess.run([sys.executable,'-m','trajectory_pipeline','--help'],check=True,stdout=out)
    report=dict(source_revision=subprocess.check_output(['git','rev-parse',revision],cwd=workspace,text=True).strip(),
                isolated_committed_checkout=True,imported_files_verified=len(manifest['files']),
                trajectory_array_hashes_verified=arrays,orbital_checks=checks,ummp=ummp)
    (workspace/'runs/extraction-clean-checkout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('orbital_checks','ummp')},indent=2))
    print('Four orbital combinations and historical UMMP passed from committed files.')
