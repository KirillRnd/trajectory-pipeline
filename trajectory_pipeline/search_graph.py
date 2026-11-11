"""Small, persistent genetic search over existing trajectory operations.

Genes choose a plan, not costates. Verified nodes survive failed improvements.
All physical changes are confined to the declared finite design space.
"""
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter
import json
import random
import subprocess
import sys
import math
import numpy as np
from .data import Trajectory, Scales, sha256, write_json
from .problem import Mission
from .contract import digest, specification, audit_configuration, make_request, configuration_hash
from .bounded import verify_bounded
from .kiam_verification import verify_kiam_psi


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def physical_spec(mission):
    result=specification(mission)
    result.pop('case_id')
    return result


def verify_cached(cached):
    if cached['status'] in ('completed','intermediate') and not cached.get('artifact'):
        raise ValueError('Missing verified graph artifact')
    if cached.get('artifact'):
        path=Path(cached['artifact'])
        if sha256(path/'trajectory.json')!=cached['metadata_sha256'] or sha256(path/'trajectory.npz')!=cached['arrays_sha256']:
            raise ValueError('Cached artifact changed')


def check_result(result, mission):
    audit_configuration(result, mission, make_request(mission), require_final=True)
    check, kiam = verify_bounded(result), verify_kiam_psi(result)
    if not check['passed'] or not kiam['passed']:
        raise ValueError('Independent physical/KIAM acceptance failed')
    return check, kiam


def supported(mission):
    if mission.center.lower() != 'sun' or any(getattr(mission, k) is not None for k in
        ('lunar','capture','parking_departure','orbital_maneuvers','arrival_offset_state_si','departure_offset_state_si')):
        raise ValueError('Search currently supports central-field body-to-body constant F/c missions')


def validate_design(design, base):
    supported(base)
    if base.time_policy is not None:raise ValueError('Declare time search bounds in the design, not in the base mission')
    axis='angular_branches' if 'angular_branches' in design else 'duration_factors'
    if axis=='duration_factors' and base.tof_days is None:raise ValueError('Fixed-time design requires tof_days')
    required = {'date_offsets_days',axis,'engines','mass_alphas','routes',
                'population','generations','seed','wall_budget_s','node_budget_s','release_budget_s','time_bounds_factors'}
    optional={'intermediate_release_budget_s','physical_continue_budget_s','intermediate_rounds'}
    if not required<=set(design) or set(design)-required-optional:raise ValueError('Search design keys differ: '+str(set(design)^required))
    for key in ('date_offsets_days',axis,'mass_alphas','time_bounds_factors'):
        values=design[key]
        if not isinstance(values,list) or not values or not all(type(x) in (int,float) and math.isfinite(x) for x in values):
            raise ValueError('Invalid finite search axis: '+key)
    if any(not 0<x<1 for x in design['mass_alphas']):raise ValueError('Invalid alpha')
    if axis=='angular_branches':
        if any(type(x) is not int or x<0 for x in design[axis]):raise ValueError('Invalid ILTT branch ranks')
    elif any(x<=0 for x in design[axis]):raise ValueError('Invalid duration')
    if len(design['time_bounds_factors'])!=2:raise ValueError('Two time bounds required')
    lo,hi=design['time_bounds_factors']
    seeds=[1.] if axis=='angular_branches' else design[axis]
    if not 0<lo<min(seeds)<=max(seeds)<hi:raise ValueError('Time bounds must enclose all seeds')
    if not design['routes'] or not set(design['routes'])<= {'fixed','release','intermediate'}:raise ValueError('Unsupported route')
    if type(design.get('intermediate_rounds',1)) is not int or not 1<=design.get('intermediate_rounds',1)<=4:raise ValueError('Invalid intermediate rounds')
    for key in ('population','generations','seed'):
        if type(design[key]) is not int or design[key] < (0 if key=='seed' else 1):raise ValueError('Invalid '+key)
    for key in ('wall_budget_s','node_budget_s','release_budget_s'):
        if type(design[key]) not in (int,float) or not math.isfinite(design[key]) or design[key]<=0:raise ValueError('Invalid '+key)
    for key in optional-{'intermediate_rounds'}:
        if key in design and (type(design[key]) not in (int,float) or not math.isfinite(design[key]) or design[key]<=0):raise ValueError('Invalid '+key)
    if not design['engines']:raise ValueError('Declare at least one engine')
    for engine in design['engines']:
        if set(engine)!= {'name','thrust_N','exhaust_velocity_m_s'} or not isinstance(engine['name'],str):raise ValueError('Declare named F/c engine pairs')
        replace(base,spacecraft=dict(base.spacecraft,**{k:v for k,v in engine.items() if k!='name'})).validate()


def learn_history(roots, base):
    """Count observed routes, retain provenance, and discover reusable physical PSI."""
    references=[]; seen=set(); counts={key:dict(attempts=0,successes=0) for key in ('fixed','release','intermediate')}
    evidence=[]
    for root in roots:
        root=Path(root)
        if not root.is_dir():raise ValueError('History directory missing: '+str(root))
        graph_path=root/'graph.json'
        if graph_path.exists():
            graph=read(graph_path)
            for key,node in graph['nodes'].items():
                if node['status'] not in ('completed','partial','failed','initial_failed'):continue
                route='intermediate' if node['request']['operation'] in ('intermediate_release','physical_continue') else 'release' if node['request']['operation'] in ('release','r_release') else 'fixed'
                counts[route]['attempts']+=1;counts[route]['successes']+=int(node['status']=='completed')
                evidence.append(dict(path=str(graph_path),sha256=sha256(graph_path),node=key,route=route,status=node['status']))
        for path in ([] if graph_path.exists() else sorted(root.rglob('summary.json'))):
            data=read(path)
            if data.get('status') not in ('completed','partial','failed','initial_failed'):continue
            if not (path.parent/'mission.json').exists():continue
            route='release' if read(path.parent/'mission.json').get('time_policy') is not None else 'fixed'
            counts[route]['attempts']+=1
            counts[route]['successes']+=int(data['status']=='completed')
            evidence.append(dict(path=str(path),sha256=sha256(path),route=route,status=data['status']))
        for path in sorted(root.rglob('trajectory.json')):
            meta=read(path); spec=meta.get('mission',{}); model=meta.get('bounded_model',{})
            if meta.get('stage')!='psi' or meta.get('status')!='verified_extremal' or not model.get('variable_mass') or model.get('alpha')!=1 or model.get('beta')!=1 or model.get('gravity_spec') is not None:continue
            if any(spec.get(k)!=getattr(base,k) for k in ('departure','target','mode')):continue
            arrays=path.with_suffix('.npz')
            if not arrays.exists():continue
            identity=(sha256(path),sha256(arrays))
            if identity in seen:continue
            seen.add(identity)
            candidate=Mission(**spec)
            try:
                supported(candidate)
                check_result(Trajectory.load(path.parent),candidate)
            except (ValueError,RuntimeError):continue
            references.append(dict(path=str(path.parent),metadata_sha256=identity[0],arrays_sha256=identity[1],mission=candidate.to_dict()))
    order=sorted(counts,key=lambda k:-(counts[k]['successes']+1)/(counts[k]['attempts']+2))
    return dict(counts=counts,template_order=order,evidence=evidence,references=references,
                note='Observed frequencies are priors, not probabilities of physical reachability; unknown routes retain exploration.')


def dimensions(design, history):
    axis='angular_branches' if 'angular_branches' in design else 'duration_factors'
    return [len(design[k]) for k in ('date_offsets_days',axis,'engines','mass_alphas','routes')]+[1+len(history['references'])]


def decode(base, design, genome):
    day,tof,engine,alpha,route,source=genome
    hardware=design['engines'][engine]
    mission=replace(base,time_policy=None,
        launch_tdb=(datetime.fromisoformat(base.launch_tdb)+timedelta(days=design['date_offsets_days'][day])).isoformat(),
        tof_days=base.tof_days if 'angular_branches' in design else base.tof_days*design['duration_factors'][tof],
        spacecraft=dict(base.spacecraft,thrust_N=hardware['thrust_N'],exhaust_velocity_m_s=hardware['exhaust_velocity_m_s']),
        solver=dict({k:v for k,v in base.solver.items() if k!='iltt_resolved'},
                    irt_entry='date' if 'angular_branches' in design else 'fixed_time',
                    iltt_branch=design.get('angular_branches',[0])[tof] if 'angular_branches' in design else 0,
                    pipeline_pazov_alpha=design['mass_alphas'][alpha],psi_mass_alpha=design['mass_alphas'][alpha]))
    return mission.validate(),design['routes'][route],source


def repair(genome, base, design, history):
    genome=list(genome)
    if 'angular_branches' in design:
        genome[-1]=0  # Legacy references do not certify the requested ILTT phase branch.
        return genome
    mission,_,source=decode(base,design,genome)
    if source:
        reference=Mission(**history['references'][source-1]['mission'])
        a,b=physical_spec(mission),physical_spec(reference)
        # R adapter currently transfers dates only. Never relabel a different engine.
        a.pop('launch_tdb');b.pop('launch_tdb')
        if a!=b:genome[-1]=0
    return genome


def breed(population, scores, sizes, rng, repair_fn):
    ranked=sorted(range(len(population)),key=lambda i:scores[i],reverse=True)
    result=[population[ranked[0]]]; events=[dict(kind='elite',parents=[ranked[0]])]
    while len(result)<len(population):
        def select():
            pool=rng.sample(range(len(population)),min(3,len(population)))
            return max(pool,key=lambda i:scores[i])
        left,right=select(),select()
        child=[rng.choice(pair) for pair in zip(population[left],population[right])]
        axis=rng.choice([i for i,n in enumerate(sizes) if n>1]) if max(sizes)>1 else 0
        if sizes[axis]>1:child[axis]=(child[axis]+rng.randrange(1,sizes[axis]))%sizes[axis]
        for i,n in enumerate(sizes):
            if rng.random()<.15:child[i]=rng.randrange(n)
        child=repair_fn(child)
        result.append(child);events.append(dict(kind='crossover_mutation',parents=[left,right],mutation_axis=axis))
    return result,events


def changes(base, result):
    a,b=physical_spec(base),physical_spec(result)
    return {k:dict(requested=a.get(k),actual=b.get(k)) for k in a if a.get(k)!=b.get(k) and not (k=='tof_days' and a.get(k) is None)}


def objectives(base, actual, fuel):
    deviation=(abs(actual.launch_jd-base.launch_jd)/365.+(abs(actual.tof_days/base.tof_days-1) if base.tof_days else 0.)+
               abs(actual.spacecraft['thrust_N']/base.spacecraft['thrust_N']-1)+
               abs(actual.spacecraft['exhaust_velocity_m_s']/base.spacecraft['exhaust_velocity_m_s']-1))
    return [deviation,float(fuel),actual.tof_days]


def pareto(rows):
    return [r for r in rows if not any(all(x<=y for x,y in zip(q['objectives'],r['objectives'])) and
        any(x<y for x,y in zip(q['objectives'],r['objectives'])) for q in rows)]


def save_intermediate(result, folder, status, phase, **extra):
    """A verified checkpoint is reusable, but is never a physical solution."""
    record=dict(status=status,phase=phase,**extra)
    if result is not None:
        record.update(last_model=result.metadata.get('bounded_model'),mission=result.metadata['mission'])
        try:
            from .intermediate_time import verify_intermediate
            verify_intermediate(result)
            path=folder/'intermediate';result.save(path)
            record.update(artifact=str(path),metadata_sha256=sha256(path/'trajectory.json'),arrays_sha256=sha256(path/'trajectory.npz'))
        except (ValueError,RuntimeError) as exc:
            record['intermediate_unavailable']=str(exc)
    if status=='intermediate' and not record.get('artifact'):
        record.update(status='failed',error='Intermediate checkpoint did not pass verification: '+record.get('intermediate_unavailable','missing source'))
    write_json(folder/'result.json',record)


def worker(request_path):
    request=read(request_path);folder=Path(request_path).parent
    mission=Mission(**request['mission']).validate();operation=request['operation'];started=perf_counter()
    try:
        if request.get('parent_artifact'):
            path=Path(request['parent_artifact'])
            if sha256(path/'trajectory.npz')!=request['parent_sha256'] or sha256(path/'trajectory.json')!=request['parent_metadata_sha256']:
                raise ValueError('Parent artifact changed')
        if operation=='cold':
            from .runner import run_pipeline
            result,status=run_pipeline(mission,folder/'run')
            if result is not None and mission.solver.get('irt_entry')=='date':
                mission=replace(mission,tof_days=result.metadata['mission']['tof_days'])
            if status['status']!='completed':
                save_intermediate(result,folder,status['status'],status['phase'],error=status.get('error'),
                    checkpoint=str(folder/'run'),elapsed_s=perf_counter()-started)
                return
        elif operation=='intermediate_release':
            from .intermediate_time import release_intermediate_duration
            source=Trajectory.load(request['parent_artifact'])
            audit_configuration(source,mission,make_request(mission))
            result=release_intermediate_duration(source,request['bounds_days'],started+request['budget_s'],folder/'duration')
            save_intermediate(result,folder,'intermediate','intermediate_release',elapsed_s=perf_counter()-started,
                              duration_search=result.metadata['intermediate_time'])
            return
        elif operation=='physical_continue':
            from .intermediate_time import continue_physical_model
            source=Trajectory.load(request['parent_artifact'])
            audit_configuration(source,mission,make_request(mission))
            result,status=continue_physical_model(source,folder/'continuation')
            if status['status']!='completed':
                save_intermediate(result,folder,'partial',status['phase'],checkpoint=str(folder/'continuation'),elapsed_s=perf_counter()-started)
                return
        elif operation in ('reference','r_transfer','r_release'):
            ref=request['reference'];path=Path(ref['path'])
            if sha256(path/'trajectory.json')!=ref['metadata_sha256'] or sha256(path/'trajectory.npz')!=ref['arrays_sha256']:raise ValueError('Reference changed')
            source=Trajectory.load(path);original=Mission(**source.metadata['mission'])
            check_result(source,original)
            if operation=='reference':
                if physical_spec(original)!=physical_spec(mission):raise ValueError('Reference physical request differs')
                result=source
                result.metadata.update(mission=mission.to_dict(),case_id=mission.case_id,configuration_sha256=configuration_hash(mission))
            else:
                old,new=physical_spec(original),physical_spec(mission)
                old.pop('launch_tdb');new.pop('launch_tdb')
                if old!=new:raise ValueError('R transfer adapter only supports a changed launch date')
                from .date_sweep import _seed, _date_context
                from .bangbang import solve_bangbang
                body,target,scale=mission.boundary()
                guess,transform=_seed(source,np.asarray(source.metadata['body_initial_state_si']),body,Scales(**source.metadata['scales']),scale)
                context,model=_date_context(mission,body,target,scale)
                context.metadata['bounded_model']=asdict(model)
                if operation=='r_release':
                    from .free_time import release_duration, audit_time_result
                    result=release_duration(context,guess,request['bounds_days'],started+request['budget_s'])
                    audit_time_result(result,replace(mission,time_policy=dict(bounds_days=request['bounds_days'])))
                else:result=solve_bangbang(context,guess,model,started+request['budget_s'],'psi')
                write_json(folder/'transport.json',dict(matrix=transform.tolist(),reference=str(path)))
        elif operation=='release':
            from .free_time import release_duration, audit_time_result
            source=Trajectory.load(request['parent_artifact'])
            check_result(source,mission)
            result=release_duration(source,source,request['bounds_days'],started+request['budget_s'])
            audit_time_result(result,replace(mission,time_policy=dict(bounds_days=request['bounds_days'])))
        else:raise ValueError('Unknown graph operation')
        actual=Mission(**result.metadata['mission'])
        # Reference reuse must match all physical conditions, not just target name.
        if operation not in ('release','r_release'):audit_configuration(result,mission,make_request(mission),require_final=True)
        check,kiam=check_result(result,actual)
        result.metadata.update(verification=check,kiam_verification=kiam)
        result.save(folder/'final')
        write_json(folder/'result.json',dict(status='completed',phase='final',mission=actual.to_dict(),
            fuel_kg=check['fuel_kg'],verification=check,kiam_verification=kiam,elapsed_s=perf_counter()-started,
            artifact=str(folder/'final'),metadata_sha256=sha256(folder/'final/trajectory.json'),arrays_sha256=sha256(folder/'final/trajectory.npz')))
    except Exception as exc:
        write_json(folder/'result.json',dict(status='failed',phase=operation,error=type(exc).__name__+': '+str(exc),elapsed_s=perf_counter()-started))


def run_search(mission_path, design_path, history_roots, output, resume=False):
    from fcntl import flock, LOCK_EX, LOCK_NB
    from .runtime import runtime_environment
    base=Mission.load(mission_path);design=read(design_path);validate_design(design,base)
    root=Path(output);root.mkdir(parents=True,exist_ok=resume)
    lock=(root/'search.lock').open('a');flock(lock,LOCK_EX|LOCK_NB)
    code_root=Path(__file__).parent
    identity=dict(mission=base.to_dict(),design=design,history_roots=[str(Path(p)) for p in history_roots],
                  runtime=runtime_environment(),code={p.name:sha256(p) for p in sorted(code_root.glob('*.py'))})
    if resume:
        if read(root/'request.json')!=identity:raise ValueError('Search resume differs in request, source or environment')
        history=read(root/'history.json');state=read(root/'graph.json')
        for cached in state['nodes'].values():verify_cached(cached)
    else:
        write_json(root/'request.json',identity)
        history=learn_history(history_roots,base);write_json(root/'history.json',history)
        sizes=dimensions(design,history);rng=random.Random(design['seed'])
        axis='angular_branches' if 'angular_branches' in design else 'duration_factors'
        zero=[min(range(len(design[k])),key=lambda i:abs(design[k][i]-value)) for k,value in
              [('date_offsets_days',0),(axis,0 if axis=='angular_branches' else 1)]]
        preferred=next(r for r in history['template_order'] if r in design['routes'])
        first=zero+[0,min(range(len(design['mass_alphas'])),key=lambda i:abs(design['mass_alphas'][i]-.5)),design['routes'].index(preferred),0]
        for index in range(len(history['references'])):
            trial=repair(first[:-1]+[index+1],base,design,history)
            if trial[-1]:first=trial;break
        population=[repair(first,base,design,history)]
        # Historical references and different hardware are genuine initial templates.
        if first[-1] and len(design['routes'])>1 and len(population)<design['population']:
            trial=list(first);trial[4]=(trial[4]+1)%len(design['routes']);population.append(trial)
        for engine in range(1,len(design['engines'])):
            if len(population)>=design['population']:break
            item=list(first);item[2]=engine;population.append(repair(item,base,design,history))
        while len(population)<design['population']:
            if first[-1] and len(design['date_offsets_days'])>1 and len(population)==design['population']-1:
                trial=list(first);trial[0]=(trial[0]+1)%sizes[0]
            else:trial=[rng.randrange(n) for n in sizes]
            population.append(repair(trial,base,design,history))
        state=dict(nodes={},edges=[],generations=[dict(population=population,results=[],origin='history_and_exploration')],
                   solutions=[],pareto=[],elapsed_s=0.,status='running')
        write_json(root/'graph.json',state)
    start=perf_counter();remaining=design['wall_budget_s']-state['elapsed_s'];deadline=start+max(0,remaining)
    def save():
        state['elapsed_s']+=perf_counter()-save.last;save.last=perf_counter();write_json(root/'graph.json',state)
    save.last=start
    def node(operation,mission,reference=None,parent=None):
        request=dict(operation=operation,mission=mission.to_dict(),budget_s=design['node_budget_s'],reference=reference)
        anchor=mission.solver.get('iltt_resolved',{}).get('tof_days',base.tof_days) if 'angular_branches' in design else base.tof_days
        if operation=='r_release':request.update(bounds_days=[x*base.tof_days for x in design['time_bounds_factors']],budget_s=design['release_budget_s'])
        if parent:
            request.update(parent_artifact=state['nodes'][parent]['artifact'],parent_sha256=state['nodes'][parent]['arrays_sha256'],
                           parent_metadata_sha256=state['nodes'][parent]['metadata_sha256'],
                           bounds_days=[x*anchor for x in design['time_bounds_factors']],budget_s=design['release_budget_s'])
        if operation=='intermediate_release':request['budget_s']=design.get('intermediate_release_budget_s',design['release_budget_s'])
        if operation=='physical_continue':request['budget_s']=design.get('physical_continue_budget_s',design['node_budget_s'])
        key=digest(request)[:24]
        if key in state['nodes']:
            cached=state['nodes'][key]
            verify_cached(cached)
            state['edges'].append(dict(parent=parent,child=key,operation=operation,cache_hit=True));save();return key
        if perf_counter()>=deadline:raise TimeoutError('Search wall budget reached')
        folder=root/'nodes'/key;folder.mkdir(parents=True)
        write_json(folder/'request.json',request)
        state['nodes'][key]=dict(status='interrupted',phase=operation,request=request,error='Worker did not finish')
        state['edges'].append(dict(parent=parent,child=key,operation=operation,cache_hit=False));save()
        timeout=min(deadline-perf_counter(),request['budget_s']+10)
        with (folder/'worker.log').open('w') as log:
            try:
                process=subprocess.run([sys.executable,'-m','trajectory_pipeline','_search-worker',str(folder/'request.json')],stdout=log,stderr=subprocess.STDOUT,timeout=max(.01,timeout))
                result=read(folder/'result.json') if (folder/'result.json').exists() else dict(status='failed',phase=operation,error='Worker exit '+str(process.returncode))
            except subprocess.TimeoutExpired:
                result=dict(status='failed',phase=operation,error='Worker wall-time budget reached')
        state['nodes'][key]=dict(result,request=request)
        if result['status']=='completed':
            actual=Mission(**result['mission']);delta=changes(base,actual)
            solution=dict(node=key,artifact=result['artifact'],changes=delta,original_conditions=not delta,
                          objectives=objectives(base,actual,result['fuel_kg']))
            state['solutions'].append(solution);state['pareto']=pareto(state['solutions'])
        save();print(base.case_id,operation,key,result['status'],flush=True);return key
    try:
        for generation in range(design['generations']):
            if generation>=len(state['generations']):break
            current=state['generations'][generation]
            for genome in current['population'][len(current['results']):]:
                mission,route,source=decode(base,design,genome)
                reference=history['references'][source-1] if source else None
                operation='cold'
                if reference:operation='reference' if physical_spec(mission)==physical_spec(Mission(**reference['mission'])) else 'r_transfer'
                fixed=node(operation,mission,reference=reference);terminal=fixed;physical_parent=fixed
                if route in ('release','intermediate') and state['nodes'][fixed]['status']=='completed':
                    terminal=node('release',Mission(**state['nodes'][fixed]['mission']),parent=fixed)
                elif route=='release' and reference:
                    terminal=node('r_release',mission,reference=reference)
                elif route=='intermediate' and state['nodes'][fixed].get('artifact'):
                    for _ in range(design.get('intermediate_rounds',1)):
                        parent=terminal
                        released=node('intermediate_release',Mission(**state['nodes'][parent]['mission']),parent=parent)
                        if state['nodes'][released]['status']!='intermediate':break
                        terminal=node('physical_continue',Mission(**state['nodes'][released]['mission']),parent=released)
                        if state['nodes'][terminal]['status']=='completed':
                            physical_parent=terminal  # Retain it if final time improvement fails.
                            terminal=node('release',Mission(**state['nodes'][terminal]['mission']),parent=terminal)
                            break
                        if not state['nodes'][terminal].get('artifact'):break
                # A failed improvement must never erase a feasible parent.
                accepted=terminal if state['nodes'][terminal]['status']=='completed' else physical_parent
                if state['nodes'][accepted]['status']!='completed' and state['nodes'][terminal].get('artifact'):
                    accepted=terminal
                result=state['nodes'][accepted]
                if result['status']=='completed':
                    score=[1]+[-x for x in objectives(base,Mission(**result['mission']),result['fuel_kg'])]
                else:
                    model=result.get('last_model') or {}
                    score=[0,{'irt':1,'departure':2,'pazov':3,'psi':4,'mass':4,'mass_and_thrust':4,'physical_thrust_limit':4,'fuel':4}.get(result.get('phase'),0),model.get('beta',0),model.get('alpha',0)]
                current['results'].append(dict(genome=genome,fixed_node=fixed,terminal_node=terminal,retained_node=accepted,score=score));save()
            if generation+1<design['generations'] and len(state['generations'])==generation+1:
                population,events=breed(current['population'],[r['score'] for r in current['results']],dimensions(design,history),
                    random.Random(design['seed']+generation+1),lambda g:repair(g,base,design,history))
                state['generations'].append(dict(population=population,results=[],origin=events));save()
        state['status']='finished'
    except TimeoutError as exc:state.update(status='budget_exhausted',stop_reason=str(exc))
    finally:save();lock.close()
    summary=dict(status=state['status'],evaluated=sum(len(g['results']) for g in state['generations']),
                 nodes=len(state['nodes']),cache_hits=sum(e['cache_hit'] for e in state['edges']),
                 accepted=len(state['solutions']),original_conditions_found=any(s['original_conditions'] for s in state['solutions']),
                 pareto=state['pareto'],elapsed_s=state['elapsed_s'],physically_unreachable_proven=False)
    summary['accepted_configurations']=len({digest(physical_spec(Mission(**state['nodes'][s['node']]['mission']))) for s in state['solutions']})
    write_json(root/'summary.json',summary)
    lines=['# Граф поиска траекторий','',f'Статус: {summary["status"]}. Узлов: {summary["nodes"]}; принятых: {summary["accepted"]}; попаданий в кеш: {summary["cache_hits"]}.',
           '', 'Принятые решения сохранены независимо от неудач их улучшения. Изменения относятся к исходной постановке. Физическая недостижимость не доказывается.',
           '', '| Узел | Операция | Статус | Причина |','|---|---|---|---|']
    for key,value in state['nodes'].items():lines.append(f"| {key} | {value['request']['operation']} | {value['status']} | {str(value.get('error') or '').replace(chr(10),' ')} |")
    for s in state['solutions']:
        lines+=['',f"## Решение {s['node']}",'',f"Артефакт: `{s['artifact']}`. Изменения: `{json.dumps(s['changes'],ensure_ascii=False)}`.",
                f"Критерии [изменения условий, топливо кг, длительность сутки]: {s['objectives']}."]
    (root/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return summary
