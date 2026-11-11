from pathlib import Path
import json
from PIL import Image
from trajectory_pipeline.data import Trajectory,sha256,write_json
from trajectory_pipeline.visualization import render

rows=json.loads(Path('runs/iltt_fresh_matrix_v4_full/verified_results.json').read_text())
root=Path('output/pipeline/iltt_fresh_matrix_v4');root.mkdir(parents=True,exist_ok=True)
index=[]
for row in rows:
    selected=row['selected']
    if not selected:continue
    result=Trajectory.load(selected['artifact']);folder=root/row['case_id']
    render(result,folder)
    previews=[]
    for p in folder.glob('*.png'):
        im=Image.open(p).convert('RGB');im.thumbnail((1280,1280))
        path=p.with_suffix('.jpg')
        for quality in (85,78,70,60,50):
            im.save(path,'JPEG',quality=quality,optimize=True)
            if path.stat().st_size<=200*1024:break
        assert path.stat().st_size<=200*1024 and max(im.size)<=1600
        previews.append(dict(path=str(path),width=im.width,height=im.height,bytes=path.stat().st_size,sha256=sha256(path)))
    index.append(dict(case_id=row['case_id'],artifact=selected['artifact'],previews=previews))
write_json(root/'index.json',index)
print('Rendered accepted selected trajectories:',len(index))
