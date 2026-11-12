"""Explicit switching of IRT optimization coordinates on an accepted parent."""
from dataclasses import replace
from pathlib import Path
from .problem import Mission
from .irt import solve_irt
from .data import write_json
from .verification import verify_irt
from .contract import make_request,audit_configuration,stamp_configuration


def recoordinate_irt(source,coordinates,output):
    if source.metadata.get('stage')!='irt' or not verify_irt(source)['passed']:
        raise ValueError('Expected a verified central IRT')
    old=Mission(**source.metadata['mission'])
    if old.center.lower()!='sun' or old.lunar is not None:raise ValueError('Central heliocentric IRT only')
    audit_configuration(source,old,make_request(old))
    reference=old.solver.get('iltt_coordinate_reference',old.solver.get('iltt_resolved',{}).get('x_corrected'))
    solver={k:v for k,v in old.solver.items() if k!='iltt_resolved'}
    solver.update(irt_entry='fixed_time',irt_coordinates=coordinates,iltt_coordinate_reference=reference)
    mission=replace(old,solver=solver).validate()
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write_json(root/'source.json',source.metadata);write_json(root/'request.json',make_request(mission))
    result,diag=solve_irt(mission,costate_seed=source.metadata['costates_initial'])
    summary=dict(status='partial',coordinates=coordinates,diagnostics=diag)
    if result is not None:
        check=verify_irt(result)
        if check['passed']:
            audit_configuration(result,mission,make_request(mission));stamp_configuration(result)
            result.metadata.update(status='verified_extremal',verification=check)
            result.save(root/'irt');summary.update(status='completed_stage',last_result='irt',verification=check)
    write_json(root/'summary.json',summary)
    return summary
