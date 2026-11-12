"""Executable component map and skill-link/CLI consistency audit."""
import ast
from datetime import datetime,timezone
from pathlib import Path
import re
from urllib.parse import unquote
from .data import sha256,write_json

ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=[
    ('ephemerides',['coverage','cache'],['test_pipeline_foundation.py','test_orbit_sources.py'],'Kepler or full ephemerides; extrapolation allowed'),
    ('iltt_irt',['solve-irt','sweep-irt','recoordinate-irt'],['test_iltt_date_entry.py','test_iltt_coordinates.py'],'date/phase/angular branch; costates first, ILTT fallback and back'),
    ('departure',['departure'],['test_pipeline_departure.py'],'hyperbolic excess continuation'),
    ('physical_psi',['pazov','psi','solve'],['test_pipeline_physical.py','test_audit_routes.py'],'intermediate reserve differs from final physical admission'),
    ('source_transition',['reconcile-irt','solve'],['test_orbit_sources.py'],'early Kepler IRT -> reconciled full ephemerides -> physical models'),
    ('orbital',['solve','verify-orbital','render-orbital'],['test_orbital_modes.py','test_angular_capture.py'],'four maneuver combinations; full re-stitching per duration trial'),
    ('ummp',['ummp','verify-ummp'],['test_ummp.py'],'verified central PSI -> historical engine law; separate terminal graph edge'),
    ('r_transform',['sweep-psi'],['test_r_transform.py'],'independent transfers, costate coordinates and sensitivity'),
    ('search',['search'],['test_search_graph.py','test_intermediate_time.py'],'central search plus optional orbital/UMMP terminal edges; preserve PSI parent'),
    ('recovery',[],['test_audit_routes.py'],'immutable stage checkpoints, replay, bound input and bounded retries'),
    ('visualization',['render','render-orbital'],['test_pipeline_visualization.py','test_visualization_labels.py'],'saved arrays, no reoptimization'),
    ('cr3bp',[],['test_cr3bp_component.py'],'standalone normalized approximation API; no heliocentric splice or lunar mission claim'),
]


def audit():
    tree=ast.parse((ROOT/'trajectory_pipeline/__main__.py').read_text(encoding='utf-8'))
    commands={n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
              and n.func.attr=='add_parser' and n.args and isinstance(n.args[0],ast.Constant)}
    issues=[];components=[]
    for name,entries,tests,scope in COMPONENTS:
        for entry in entries:
            if entry not in commands:issues.append(f'{name}: missing command {entry}')
        for test in tests:
            if not (ROOT/'tests'/test).exists():issues.append(f'{name}: missing test {test}')
        components.append(dict(component=name,commands=entries,tests=tests,scope=scope))
    skill=ROOT/'.agents/skills/trajectory-pipeline'
    for file in sorted(skill.rglob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            target=target.split('#')[0].strip('<>')
            if not target or '://' in target:continue
            if not (file.parent/unquote(target)).exists():issues.append(f'{file.relative_to(ROOT)}: missing link {target}')
    files=list((ROOT/'trajectory_pipeline').glob('*.py'))+list((ROOT/'tests').glob('*.py'))+list(skill.rglob('*.md'))
    return dict(passed=not issues,checked_utc=datetime.now(timezone.utc).isoformat(),issues=issues,components=components,
                source_sha256={str(p.relative_to(ROOT)):sha256(p) for p in sorted(files)},
                scope='Static routing consistency; numerical acceptance requires the separate Docker audit report')


def save_audit(output):
    result=audit();write_json(Path(output),result);return result
