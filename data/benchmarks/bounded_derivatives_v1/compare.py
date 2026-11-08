from pathlib import Path
from dataclasses import asdict
from time import perf_counter
import json
import numpy as np
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.bounded import collocate

root=Path('data/benchmarks/parameter_study_v1')
output=Path('runs/bounded_derivatives_v1')
rows=[]
for case in sorted(root.iterdir()):
    if not case.is_dir() or not case.name.endswith(('__reference','__mass_x2')):continue
    choices=list((case/'stage_psi/mass').glob('point_*/trajectory.json'))
    if choices:
        previous=Trajectory.load(case/'stage_psi/mass/initial')
        source=Trajectory.load(case/'psi_source')
    else:
        choices=list((case/'stage_pazov/functional').glob('point_*/trajectory.json'))
        previous=Trajectory.load(case/'stage_pazov/functional/initial')
        source=Trajectory.load(case/'stage_departure'/json.loads((case/'stage_departure/continuation.json').read_text())['last_point'])
    target=Trajectory.load(sorted(choices)[0].parent)
    model=BoundedModel(**target.metadata['bounded_model'])
    pair=[]
    for analytic in (False,True):
        started=perf_counter()
        row=dict(case=case.name,analytic=analytic,model=asdict(model))
        try:
            result=collocate(source,previous,model,started+20,target.metadata['stage'],analytic_derivatives=analytic)
            row.update(passed=True,verification=result.metadata['verification'],nodes=result.metadata.get('collocation_nodes'),
                       corrector=result.metadata.get('corrector','collocation'))
            result.save(output/case.name/('analytic' if analytic else 'finite'))
            pair.append(result)
        except Exception as exc:
            row.update(passed=False,error=f'{type(exc).__name__}: {exc}')
        row['wall_s']=perf_counter()-started
        rows.append(row)
        write_json(output/'comparison.json',rows)
        print(case.name,analytic,row['passed'],round(row['wall_s'],3),flush=True)
    if len(pair)==2:
        difference=float(np.linalg.norm(pair[0].arrays['r_m']-pair[1].arrays['r_m'],axis=1).max())
        for row in rows[-2:]:row['paired_position_difference_m']=difference
        write_json(output/'comparison.json',rows)
