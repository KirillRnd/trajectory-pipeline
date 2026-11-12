import json,time,traceback
from pathlib import Path
from dataclasses import replace
from trajectory_pipeline.data import Trajectory,write_json
from trajectory_pipeline.bounded_model import BoundedModel
from trajectory_pipeline.bangbang import solve_bangbang
from trajectory_pipeline.kiam_verification import verify_kiam_psi
root=Path('runs/apophis_daily_routes_v1/chains/2028-02-23')
source=Trajectory.load(root/'continue_0/fuel/initial')
out=root/'direct_exact_probe';out.mkdir(exist_ok=False)
write_json(out/'request.json',dict(source='continue_0/fuel/initial',budget_s=45,route='Exact alpha=1 attempt from verified time-released intermediate, no parameter changes'))
try:
    model=replace(BoundedModel(**source.metadata['bounded_model']),alpha=1.)
    result=solve_bangbang(source,source,model,time.perf_counter()+45,'psi')
    check=verify_kiam_psi(result);assert check['passed'];result.metadata['kiam_verification']=check
    result.save(out/'result');write_json(out/'summary.json',dict(status='accepted',last_result='result'))
except Exception as exc:
    write_json(out/'summary.json',dict(status='failed',error=str(exc)));(out/'error.log').write_text(traceback.format_exc())
print((out/'summary.json').read_text())
