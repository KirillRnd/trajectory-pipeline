"""Declarative parameter variations and request-to-result audit of real runs."""
from copy import deepcopy
from datetime import datetime,timedelta
from pathlib import Path
import csv
import json
import numpy as np
from .data import Trajectory,write_json,DAY_S
from .problem import Mission
from .contract import audit_configuration,configuration_hash,specification,digest
from .outcomes import describe


def build_matrix(design):
    plan=json.loads(Path(design).read_text(encoding='utf-8'))
    bases={m['case_id']:m for m in json.loads(Path(plan['base_matrix']).read_text(encoding='utf-8'))}
    rows=[];identities=set()
    policies=[bases[key].get('solver',{}) for key in plan['base_cases']]
    if any(policy!=policies[0] for policy in policies):raise ValueError('Parameter study requires a common solver policy')
    allowed={'mass_kg','tof_days','vinf_max_m_s','spacecraft.thrust_N','spacecraft.exhaust_velocity_m_s','spacecraft.dry_mass_kg'}
    for key in plan['base_cases']:
        for variant in plan['variants']:
            mission=deepcopy(bases[key])
            mission['case_id']=key+'__'+variant['name']
            if mission['case_id'] in identities:raise ValueError('Duplicate parameter-study identity')
            identities.add(mission['case_id'])
            for path,factor in variant.get('multiply',{}).items():
                if path not in allowed:raise ValueError('Parameter design cannot alter solver policy or unsupported fields: '+path)
                if not isinstance(factor,(int,float)) or isinstance(factor,bool) or not np.isfinite(factor) or factor<=0:raise ValueError('Multipliers must be finite and positive numbers')
                parts=path.split('.');target=mission
                for part in parts[:-1]:target=target[part]
                if parts[-1] not in target:raise ValueError('Unknown variation path: '+path)
                target[parts[-1]]*=factor
            shift=variant.get('launch_shift_days',0)
            if not isinstance(shift,(int,float)) or isinstance(shift,bool) or not np.isfinite(shift):raise ValueError('Launch shift must be a finite number of TDB days')
            if shift:
                mission['launch_tdb']=(datetime.fromisoformat(mission['launch_tdb'])+timedelta(days=shift)).isoformat()
            rows.append(Mission(**mission).validate().to_dict())
    return rows


def report_study(design,source,output):
    source=Path(source);output=Path(output)
    planned=build_matrix(design)
    recorded=json.loads((source/'matrix.json').read_text(encoding='utf-8'))
    if planned!=recorded:raise ValueError('Study run does not match the declared parameter design')
    rows=[];groups={};by_base={};requests={};artifact_count=0
    lines=['# Проверка параметров и равномерности траекторного пайплайна','',
           'Одинаковые варианты двигателя, массы и геометрии применены ко всем базовым миссиям. Численные правила общие; отдельные строки не подгонялись.','',
           '| Случай | m₀, кг | F, мН | c, км/с | Статус | Блок | Причина остановки | Проверено этапов | Финальные параметры |',
           '|---|---:|---:|---:|---|---|---|---:|---|']
    for cfg in recorded:
        mission=Mission(**cfg);key=mission.case_id;base,variant=key.rsplit('__',1)
        folder=source/key
        summary=json.loads((folder/'summary.json').read_text(encoding='utf-8')) if (folder/'summary.json').exists() else {}
        ledger=json.loads((folder/'parameter_audit.json').read_text(encoding='utf-8')) if (folder/'parameter_audit.json').exists() else {}
        status=summary.get('status','pending')
        stages=ledger.get('stages',[])
        requested=cfg['spacecraft']
        row=dict(case_id=key,base_case=base,variant=variant,status=status,phase=summary.get('phase'),
                 mass_kg=cfg['mass_kg'],thrust_N=requested['thrust_N'],exhaust_velocity_m_s=requested['exhaust_velocity_m_s'],
                 dry_mass_kg=requested['dry_mass_kg'],launch_tdb=cfg['launch_tdb'],tof_days=cfg['tof_days'],
                 requested_configuration_sha256=configuration_hash(mission),audited_stages=len(stages),
                 final_parameters_match=None,configuration_error=False)
        outcome=describe(folder,cfg)
        row.update(pipeline_block=outcome['block'],stop_kind=outcome['stop_kind'],stop_label=outcome['stop_label'],
                   stop_reason=outcome['reason'],last_rejection=outcome['last_rejection'],
                   last_verified_artifact=outcome['last_verified_artifact'],last_model=outcome['last_model'])
        request_path=folder/'request.json'
        if request_path.exists():
            request=json.loads(request_path.read_text(encoding='utf-8'))
            payload={k:v for k,v in request.items() if k!='request_sha256'}
            if request['request_sha256']!=digest(payload) or request['mission']!=specification(mission):
                raise ValueError('Request manifest differs from the declared parameter matrix: '+key)
            if not np.isclose(request['epoch_jd'],mission.launch_jd,rtol=0,atol=1e-9) or not np.isclose(request['tof_s'],mission.tof_days*DAY_S,rtol=1e-12,atol=1e-6):
                raise ValueError('Request epochs differ from the declared dates: '+key)
            requests[key]=request
            r0=np.asarray(request['body_initial_state_si'])[:3];rf=np.asarray(request['target_state_si'])[:3]
            angle=np.degrees(np.arccos(np.clip(np.dot(r0,rf)/np.linalg.norm(r0)/np.linalg.norm(rf),-1.,1.)))
            row['boundary_transfer_angle_deg']=float(angle)
            checked=0
            for artifact_path in folder.rglob('trajectory.json'):
                artifact=Trajectory.load(artifact_path.parent)
                audit_configuration(artifact,mission,request,require_final=artifact_path.parent.name=='final')
                checked+=1
            row['audited_artifacts']=checked;artifact_count+=checked
        if status=='completed':
            artifact=Trajectory.load(folder/'final')
            request=json.loads((folder/'request.json').read_text(encoding='utf-8'))
            check=audit_configuration(artifact,mission,request,require_final=True)
            row.update(final_parameters_match=check['passed'],actual_thrust_N=check['recovered_model']['model_thrust_N'],
                       actual_exhaust_velocity_m_s=check['recovered_model']['exhaust_velocity_m_s'],
                       actual_initial_mass_kg=float(artifact.arrays['mass_kg'][0]),fuel_kg=summary['verification']['fuel_kg'])
        else:
            error=summary.get('error','')
            row.update(error=error,configuration_error='Configuration mismatch' in error or 'request/boundary manifest differs' in error)
        for group,keygroup in ((groups,variant),(by_base,base)):
            counts=group.setdefault(keygroup,dict(cases=0,completed=0,partial=0,failed=0,configuration_errors=0))
            counts['cases']+=1
            if status in counts:counts[status]+=1
            counts['configuration_errors']+=int(row['configuration_error'])
        final='совпадают' if row['final_parameters_match'] else 'несовпадение отклонено' if row['configuration_error'] else 'финал не получен'
        lines.append(f"| {key} | {cfg['mass_kg']:g} | {requested['thrust_N']*1000:g} | {requested['exhaust_velocity_m_s']/1000:g} | {status} | {outcome['block']} | {outcome['stop_label']} | {len(stages)} | {final} |")
        rows.append(row)
    lines+=['','## Равномерность по вариантам','',
            '| Вариант | Полных ПСИ / случаев | Частичных | Ошибок | Несовпадений параметров |',
            '|---|---:|---:|---:|---:|']
    for key,count in groups.items():lines.append(f"| {key} | {count['completed']}/{count['cases']} | {count['partial']} | {count['failed']} | {count['configuration_errors']} |")
    lines+=['','## Равномерность по геометриям','',
            '| Базовая миссия | Полных ПСИ / случаев | Частичных | Ошибок |',
            '|---|---:|---:|---:|']
    for key,count in by_base.items():lines.append(f"| {key} | {count['completed']}/{count['cases']} | {count['partial']} | {count['failed']} |")
    geometry_checks=[]
    for base in by_base:
        ref=requests.get(base+'__reference')
        if ref is None:continue
        def same_state(a,b):return bool(np.all(np.abs(np.asarray(a)-np.asarray(b))<=np.r_[np.full(3,.1),np.full(3,1e-6)]))
        check=dict(base_case=base)
        for variant in ('thrust_x2','exhaust_x2','mass_x2'):
            item=requests.get(base+'__'+variant)
            if item is not None:
                check[variant+'_preserves_geometry']=same_state(ref['body_initial_state_si'],item['body_initial_state_si']) and same_state(ref['target_state_si'],item['target_state_si'])
        shifted=requests.get(base+'__launch_plus_90d')
        if shifted is not None:
            check['launch_shift_changes_geometry']=not same_state(ref['body_initial_state_si'],shifted['body_initial_state_si']) and not same_state(ref['target_state_si'],shifted['target_state_si'])
        longer=requests.get(base+'__duration_x1p2')
        if longer is not None:
            check['duration_preserves_departure_changes_arrival']=same_state(ref['body_initial_state_si'],longer['body_initial_state_si']) and not same_state(ref['target_state_si'],longer['target_state_si'])
        if not all(value for key,value in check.items() if key!='base_case'):raise ValueError('Variation changed geometry inconsistently: '+base)
        geometry_checks.append(check)
    lines+=['',f'Повторно проверены параметры {artifact_count} сохранённых траекторных артефактов, включая промежуточные точки. Изменение двигателя/массы сохраняет граничную геометрию; изменение даты/длительности проверяется по реальным состояниям тел.','',
            'Отсутствие несовпадений параметров подтверждает передачу конфигурации на проверенных этапах. Оно не превращает частичный путь в конечную ПСИ. Несходимость не доказывает физическую недостижимость.','']
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines),encoding='utf-8')
    result=dict(cases=len(rows),by_variant=groups,by_base=by_base,rows=rows,
                completed=sum(r['status']=='completed' for r in rows),configuration_errors=sum(r['configuration_error'] for r in rows),
                audited_artifacts=artifact_count,geometry_checks=geometry_checks,
                study_complete=all(r['status'] not in ('pending','running') for r in rows))
    write_json(output.with_suffix('.json'),result)
    with output.with_suffix('.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(dict.fromkeys(k for row in rows for k in row)))
        writer.writeheader();writer.writerows(rows)
    _plot_coverage(rows,output)
    return result


def _plot_coverage(rows,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from .visualization import preview_jpeg
    bases=list(dict.fromkeys(row['base_case'] for row in rows));variants=list(dict.fromkeys(row['variant'] for row in rows))
    labels={'reference':'Исходный','thrust_x2':'Тяга ×2','exhaust_x2':'Скорость\nистечения ×2','mass_x2':'Масса ×2\nтяга прежняя',
            'launch_plus_90d':'Старт\n+90 суток','duration_x1p2':'Длительность\n×1,2'}
    palette={'completed':('#c8e6c9','ПСИ'),'partial':('#fff0bd','Частично'),'failed':('#f3c5c5','Ошибка')}
    fig,ax=plt.subplots(figsize=(12,4.8),layout='constrained')
    for row in rows:
        x=variants.index(row['variant']);y=bases.index(row['base_case'])
        color,text=palette.get(row['status'],('#e5e5e5','Ожидание'))
        if row['status'] in ('partial','failed'):
            block=row.get('pipeline_block','')
            short={'ПСИ: введение массы':'Масса','ПСИ: физический предел тяги':'Предел тяги',
                   'ПСИ: точное управление':'Управление','Пазов: предел ускорения':'Пазов / предел',
                   'Пазов: функционал':'Пазов / цель','Начальная дополнительная скорость':'Начальная скорость'}.get(block,block)
            text+='\n'+short
        if row['configuration_error']:color,text='#d8c8f0','Параметры\nотклонены'
        ax.add_patch(plt.Rectangle((x-.5,y-.5),1,1,facecolor=color,edgecolor='white',linewidth=2))
        ax.text(x,y,text,ha='center',va='center',fontsize=11)
    names={'earth_venus_2032':'Венера, 2032','earth_mars_2028':'Марс, 2028','earth_apophis_2029':'Апофис, 2029','earth_ceres_2030':'Церера, 2030'}
    ax.set(xticks=range(len(variants)),xticklabels=[labels.get(v,v) for v in variants],yticks=range(len(bases)),
           yticklabels=[names.get(b,b) for b in bases],xlim=(-.5,len(variants)-.5),ylim=(len(bases)-.5,-.5))
    ax.tick_params(length=0,labelsize=11)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.set_title('Работоспособность по параметрам и геометрии\n'+f"Полных ПСИ: {sum(r['status']=='completed' for r in rows)}/{len(rows)}; параметры всех готовых результатов перепроверены",fontsize=14,pad=16)
    ax.legend(handles=[Patch(facecolor=c,label=t) for c,t in palette.values()],loc='upper center',bbox_to_anchor=(.5,-.17),ncol=3,frameon=False)
    prefix=output.with_name(output.stem+'_coverage')
    fig.savefig(prefix.with_suffix('.svg'));fig.savefig(prefix.with_suffix('.png'),dpi=160)
    preview_jpeg(prefix.with_suffix('.png'),prefix.with_suffix('.jpg'))
    plt.close(fig)
