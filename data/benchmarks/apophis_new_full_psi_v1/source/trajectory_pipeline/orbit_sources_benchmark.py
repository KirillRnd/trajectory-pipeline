"""Small real Apophis source-transition check; run in Linux Docker."""
import argparse
from dataclasses import replace
from pathlib import Path
from .problem import Mission
from .runner import run_irt
from .data import Trajectory,write_json
from .orbit_transition import reconcile_irt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(args.output);root.mkdir(parents=True,exist_ok=False)
    base=Mission.load('configs/apophis_new_early.json');rows=[]
    full={'earth':{'kind':'ephemerides'},'apophis':{'kind':'ephemerides'}}
    for date in ('2029-06-15','2029-06-22'):
        mission=replace(base,case_id='apophis_new_'+date,launch_tdb=date+'T00:00:00')
        path=root/date
        early=run_irt(mission,path/'early')
        row=dict(date=date,early_status=early['status'])
        if early['status']=='completed_stage':
            source=Trajectory.load(path/'early'/early['last_result'])
            result,summary=reconcile_irt(source,full,path/'full')
            row.update(transition=summary,iltt=source.metadata['mission']['solver']['iltt_resolved'])
        rows.append(row);write_json(root/'results.json',rows);print(date,row['early_status'],flush=True)
    return 0 if all(r.get('transition',{}).get('status')=='completed_stage' for r in rows) else 2

if __name__=='__main__':raise SystemExit(main())
