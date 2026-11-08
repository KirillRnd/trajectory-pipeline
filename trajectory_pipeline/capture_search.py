"""Declared angular candidate search: independently stitch every full mission.

The minimum duration is selected only among independently verified candidates
meeting the arrival and/or spacecraft fuel budget. No global optimum claim.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
from .data import Trajectory, write_json, sha256, DAY_S
from .problem import Mission
from .contract import specification, configuration_hash, digest


def candidate_mission(mission,width):
    modes=deepcopy(mission.orbital_maneuvers)
    arrival=modes['arrival'];arrival.pop('duration_search')
    arrival['capture_control']['half_width_rad']=width
    return replace(mission,orbital_maneuvers=modes)


def run_capture_search(mission,output,resume=False):
    from .orbital_pipeline import run_orbital_pipeline, verify_orbital_mission
    from .runtime import runtime_environment
    output=Path(output)
    if resume and Mission.load(output/'mission.json').to_dict()!=mission.to_dict():
        raise ValueError('Capture search resume changes the requested parameters')
    output.mkdir(parents=True,exist_ok=resume)
    write_json(output/'mission.json',mission.to_dict());write_json(output/'environment.json',runtime_environment())
    payload=dict(mission=specification(mission),configuration_sha256=configuration_hash(mission))
    write_json(output/'request.json',dict(payload,request_sha256=digest(payload)))
    rows=[]
    widths=mission.orbital_maneuvers['arrival']['duration_search']['half_widths_rad']
    for index,width in enumerate(widths):
        folder=output/'candidates'/f'{index:03d}'
        child=candidate_mission(mission,width)
        write_json(output/'summary.json',dict(status='running',phase='capture_duration_search',candidate_index=index,
                   completion_scope='initial_orbit_to_final_orbit',selection_scope='declared_candidates'))
        if resume and (folder/'summary.json').exists():
            if Mission.load(folder/'mission.json').to_dict()!=child.to_dict():raise ValueError('Saved capture candidate differs from request')
            summary=json.loads((folder/'summary.json').read_text())
        else:
            _,summary=run_orbital_pipeline(child,folder)
        row=dict(index=index,half_width_rad=width,folder=str(folder.relative_to(output)),
                 status=summary['status'],phase=summary.get('orbital_phase',summary.get('phase')),
                 error=summary.get('error'),stop_kind=summary.get('stop_kind'),summary_sha256=sha256(folder/'summary.json'))
        if (folder/'verification.json').exists():
            verification=json.loads((folder/'verification.json').read_text())
            row['budget_checks']=verification.get('capture_budget')
            row['measured_arrival_propellant_kg']=verification.get('arrival_propellant_kg')
            row['measured_total_spacecraft_propellant_kg']=verification.get('total_spacecraft_propellant_kg')
        if summary['status']=='completed':
            check=verify_orbital_mission(folder)
            if not check['passed']:raise ValueError('Completed capture candidate failed independent replay')
            final=Trajectory.load(folder/'final')
            row.update(duration_s=float(final.arrays['t_s'][-1]),final_mass_kg=check['final_mass_kg'],
                       arrival_propellant_kg=check['arrival_propellant_kg'],
                       total_spacecraft_propellant_kg=check['total_spacecraft_propellant_kg'])
        rows.append(row);write_json(output/'capture_search.json',dict(candidates=rows))
        print('capture search',index,width,row['status'],row.get('duration_s'),flush=True)
    accepted=[row for row in rows if row['status']=='completed']
    if not accepted:
        summary=dict(status='partial',phase='capture_duration_search',stop_kind='no_verified_feasible_capture_candidate',
                     error='No declared candidate completed stitching, replay and fuel/duration constraints; see capture_search.json',
                     completion_scope='initial_orbit_to_final_orbit',selection_scope='declared_candidates')
        write_json(output/'summary.json',summary)
        return None,summary
    best=min(accepted,key=lambda r:(r['duration_s'],r['index']))
    summary=dict(status='completed',phase='final',completion_scope='initial_orbit_to_final_orbit',
                 selected_folder=best['folder'],selection_scope='minimum_duration_among_verified_declared_candidates',
                 selected_half_width_rad=best['half_width_rad'],duration_days=best['duration_s']/DAY_S,
                 search_sha256=sha256(output/'capture_search.json'))
    write_json(output/'summary.json',summary)
    verification=verify_capture_search(output);write_json(output/'verification.json',verification)
    if not verification['passed']:raise ValueError('Capture search selection failed verification')
    return Trajectory.load(output/best['folder']/'final'),summary


def verify_capture_search(folder):
    from .orbital_pipeline import verify_orbital_mission
    p=Path(folder);mission=Mission.load(p/'mission.json')
    summary=json.loads((p/'summary.json').read_text());request=json.loads((p/'request.json').read_text())
    payload={k:v for k,v in request.items() if k!='request_sha256'}
    if digest(payload)!=request['request_sha256'] or payload['mission']!=specification(mission) or payload['configuration_sha256']!=configuration_hash(mission):
        raise ValueError('Capture search root request mismatch')
    if summary.get('status')!='completed':return dict(passed=False,reason='No verified feasible candidate selected')
    if summary['search_sha256']!=sha256(p/'capture_search.json'):raise ValueError('Capture search table checksum mismatch')
    rows=json.loads((p/'capture_search.json').read_text())['candidates']
    widths=mission.orbital_maneuvers['arrival']['duration_search']['half_widths_rad']
    if len(rows)!=len(widths):raise ValueError('Capture search omitted a declared candidate')
    feasible=[]
    for index,(row,width) in enumerate(zip(rows,widths)):
        relative=f'candidates/{index:03d}'
        if row['index']!=index or row['half_width_rad']!=width or row['folder']!=relative:raise ValueError('Capture search candidate identity mismatch')
        child=p/relative
        if Mission.load(child/'mission.json').to_dict()!=candidate_mission(mission,width).to_dict():raise ValueError('Candidate configuration mismatch')
        if sha256(child/'summary.json')!=row['summary_sha256']:raise ValueError('Candidate summary checksum mismatch')
        status=json.loads((child/'summary.json').read_text())['status']
        if status!=row['status']:raise ValueError('Candidate status mismatch')
        if status=='completed':
            check=verify_orbital_mission(child)
            if not check['passed']:raise ValueError('Selected search candidate is not physically verified')
            duration=float(Trajectory.load(child/'final').arrays['t_s'][-1])
            if duration!=row['duration_s']:raise ValueError('Capture search duration mismatch')
            for key in ('final_mass_kg','arrival_propellant_kg','total_spacecraft_propellant_kg'):
                if abs(row[key]-check[key])>1e-7:raise ValueError('Capture search mass accounting mismatch')
            feasible.append((duration,index,relative,check))
    if not feasible:raise ValueError('Capture search has no feasible candidate')
    best=min(feasible,key=lambda x:(x[0],x[1]))
    return dict(passed=best[2]==summary['selected_folder'] and widths[best[1]]==summary['selected_half_width_rad']
                and abs(summary['duration_days']-best[0]/DAY_S)<1e-9
                and summary['selection_scope']=='minimum_duration_among_verified_declared_candidates',
                selection_scope='minimum_duration_among_verified_declared_candidates',candidate_count=len(rows),
                feasible_count=len(feasible),selected_folder=best[2],selected_verification=best[3])
