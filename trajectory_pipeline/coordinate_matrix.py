"""Real date/target matrix for ILTT/costate correction switching, Docker only."""
import argparse,json,signal
from pathlib import Path
from dataclasses import replace
from datetime import datetime,timedelta
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .problem import Mission
from .data import DAY_S,write_json,sha256
from .iltt_entry import angular_branches,resolve_date_mission
from .iltt_coordinates import ILTTCoordinates
from .irt import solve_irt
from .verification import verify_irt
from .contract import audit_configuration,make_request,stamp_configuration


def timed_call(seconds,fn,*args,**kwargs):
    """Linux worker deadline also interrupts legacy integration inside F(x)."""
    def expired(signum,frame):raise TimeoutError('Worker wall deadline reached inside '+fn.__name__)
    remaining,interval=signal.getitimer(signal.ITIMER_REAL);started=perf_counter()
    previous=signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,min(seconds,remaining) if remaining else seconds)
    try:return fn(*args,**kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
        if remaining:signal.setitimer(signal.ITIMER_REAL,max(1e-6,remaining-(perf_counter()-started)),interval)


def phase_seed(mission):
    tb,eph,scale,initial,el,phase,branches=angular_branches(mission)
    branch=branches[mission.solver.get('iltt_branch',0)]
    lam=branch['lambda_initial'];kappa=float(el[0]);limit=.999*abs(np.sin(.642))
    _,raw=tb.make_F_function(initial[:3][None,:],initial[3:][None,:],lam,kappa,0,1,float(el[2]),float(el[3]),float(el[1]),float(el[8]),dm_limit=limit)
    # This is only a bounded approximation seed; no accepted costates are clipped.
    x=np.asarray(raw).copy();x[0]=np.clip(x[0],-limit+1e-8,limit-1e-8);x[1]=np.clip(x[1],-30+1e-8,30-1e-8)
    chart=ILTTCoordinates(initial,x,dm_limit=limit)
    days=float(2*np.pi*tb.T_a(lam,kappa)*scale.time_s/DAY_S)
    result=replace(mission,tof_days=days,solver=dict(mission.solver,irt_entry='fixed_time',iltt_coordinate_reference=x.tolist()))
    return result,chart.to_costates(x),dict(kind='unverified date/phase ILTT approximation',phase_rad=phase,branch=branch,
                                         raw_parameters=np.asarray(raw).tolist(),parameters=x.tolist(),tof_days=days)


def worker(request):
    configuration,folder=request;root=Path(folder);root.mkdir(parents=True,exist_ok=True)
    mission=Mission(**configuration).validate();write_json(root/'mission.json',mission.to_dict())
    row=dict(case_id=mission.case_id,target=mission.target,departure=mission.departure,mode=mission.mode,
             date=mission.launch_tdb,stages=[],accepted=False)
    try:
        resolved=timed_call(8,resolve_date_mission,mission)
        entry=resolved.solver['iltt_resolved'];p=np.array(entry['costates']);reference=entry['x_corrected']
        row['entry']=dict(accepted=True,tof_days=resolved.tof_days,lambda_initial=entry['lambda_initial'])
    except (ValueError,RuntimeError,TimeoutError,OverflowError,np.linalg.LinAlgError) as exc:
        row['entry']=dict(accepted=False,error=str(exc))
        try:
            resolved,p,seed=phase_seed(mission);reference=seed['parameters'];row['fallback_seed']=seed
        except Exception as seed_exc:
            row['stopped_stage']='phase_seed';row['error']=str(seed_exc)
            write_json(root/'summary.json',row);return row
    settings={k:v for k,v in resolved.solver.items() if k!='iltt_resolved'}
    settings.update(irt_entry='fixed_time',iltt_coordinate_reference=reference,compare_seeds=False,
                    budget_s=20,attempt_budget_s=20,max_nfev=70)
    resolved=replace(resolved,solver=settings)
    row['tof_days']=resolved.tof_days
    write_json(root/'resolved.json',resolved.to_dict());write_json(root/'seed.json',dict(costates=p.tolist(),reference=reference))
    # Each mode has its own budget: ILTT failure cannot consume the fallback.
    for mode in ('iltt','costates'):
        stage=dict(coordinates=mode,accepted=False)
        try:
            trial=replace(resolved,solver=dict(settings,irt_coordinates=mode))
            result,diag=timed_call(20,solve_irt,trial,costate_seed=p)
            stage['diagnostics']=diag
            if result is not None:
                check=verify_irt(result);stage['verification']=check
                audit_configuration(result,trial,make_request(trial))
                if check['passed']:
                    stage['accepted']=True;stamp_configuration(result)
                    result.metadata.update(status='verified_extremal',verification=check)
                    result.save(root/mode);p=np.asarray(result.metadata['costates_initial']);row['accepted']=True
                    row['last_result']=mode
            if result is None:
                candidates=[x['last_costates'] for x in diag.get('attempts',[]) if 'last_costates' in x]
                if candidates:p=np.asarray(candidates[-1]);stage['next_seed']='last numerical costates, not verified'
                else:stage['next_seed']='unchanged input costates'
        except (ValueError,RuntimeError,TimeoutError,OverflowError,np.linalg.LinAlgError) as exc:
            stage['error']=str(exc);stage['next_seed']='unchanged input costates'
        row['stages'].append(stage);write_json(root/'summary.json',row)
    row['rescued_by_costates']=not row['stages'][0]['accepted'] and row['stages'][1]['accepted']
    row['rescued_after_entry_failure']=not row['entry']['accepted'] and row['accepted']
    row['stopped_stage']=None if row['accepted'] else 'irt_after_both_modes'
    write_json(root/'summary.json',row);return row


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--workers',type=int,default=3);p.add_argument('--resume',action='store_true')
    args=p.parse_args();root=Path(args.output);root.mkdir(parents=True,exist_ok=args.resume)
    configs=json.loads(Path('configs/search_matrix_date_v4.json').read_text());requests=[]
    for cfg in configs:
        base=Mission(**cfg)
        for shift in (-90,0,90):
            date=(datetime.fromisoformat(base.launch_tdb)+timedelta(days=shift)).isoformat()
            settings=dict(base.solver,iltt_budget_s=8,irt_entry='date',iltt_branch=0)
            m=replace(base,case_id=base.case_id+f'_d{shift:+d}',launch_tdb=date,solver=settings)
            if m.target.lower()=='apophis':m=replace(m,orbit_sources={'earth':dict(kind='kepler',preset='EarthSimple'),'apophis':dict(kind='kepler',preset='ApophisNew')})
            requests.append((m.to_dict(),str(root/m.case_id)))
    design=dict(offsets_days=[-90,0,90],branch_rank=0,entry_budget_s=8,mode_budget_s=20,
                                      requests=[r[0] for r in requests],scope='IRT only; no PSI or fuel feasibility claim')
    if args.resume and json.loads((root/'design.json').read_text())!=design:raise ValueError('Resume design mismatch')
    write_json(root/'design.json',design)
    rows=[];pending_requests=[]
    for request in requests:
        saved=Path(request[1])/'summary.json'
        row=json.loads(saved.read_text()) if saved.exists() else {}
        if args.resume and 'stopped_stage' in row:rows.append(row)
        else:pending_requests.append(request)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending={pool.submit(worker,r):r[0]['case_id'] for r in pending_requests}
        for future in as_completed(pending):
            try:row=future.result()
            except Exception as exc:row=dict(case_id=pending[future],accepted=False,worker_error=str(exc))
            rows.append(row);write_json(root/'results.json',sorted(rows,key=lambda r:r['case_id']))
            print(row['case_id'],row['accepted'],'rescue',row.get('rescued_by_costates'),flush=True)
    write_json(root/'totals.json',dict(cases=len(rows),accepted=sum(r['accepted'] for r in rows),
        iltt_accepted=sum(bool(r.get('stages') and r['stages'][0]['accepted']) for r in rows),
        costate_rescues=sum(r.get('rescued_by_costates',False) for r in rows),
        entry_rescues=sum(r.get('rescued_after_entry_failure',False) for r in rows)))

if __name__=='__main__':main()
