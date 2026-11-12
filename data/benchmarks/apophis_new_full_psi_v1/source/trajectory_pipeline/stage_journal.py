"""Durable stage inputs, immutable outputs and bounded interruption recovery."""
import hashlib,json
from pathlib import Path
from .data import Trajectory,write_json,sha256
from .contract import digest


def identity(source):
    arrays={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in source.arrays.items()}
    metadata={k:v for k,v in source.metadata.items() if k not in ('verification','runtime','arrays_sha256')}
    return digest(dict(arrays=arrays,metadata=metadata))


def stage(root,name,source,execute,verify,*,recover=None,max_attempts=3):
    root=Path(root);request=root/(name+'_request.json');receipt=root/(name+'_receipt.json');checkpoint=root/(name+'_checkpoint')
    expected=dict(input_identity=identity(source))
    if request.exists():
        if json.loads(request.read_text())!=expected:raise ValueError('Stage input changed: '+name)
    else:write_json(request,expected)
    current=source
    if receipt.exists():
        saved=json.loads(receipt.read_text())
        checkpoint=root/saved.get('checkpoint',checkpoint.name)
        if sha256(checkpoint/'trajectory.npz')!=saved['arrays_sha256'] or sha256(checkpoint/'trajectory.json')!=saved['metadata_sha256']:
            raise ValueError('Stage checkpoint changed: '+name)
        result=Trajectory.load(checkpoint);verify(result)
        if saved['event'].get('status') in ('completed','completed_stage','recovered_checkpoint'):
            return result,saved['event']
        current=result
        checkpoint=root/(name+'_checkpoint_'+str(saved.get('attempt',1)+1))
    # Output was committed but the process died before its receipt. It is still
    # bound to the durable request; replay before accepting this transaction.
    if (checkpoint/'trajectory.json').exists():
        result=Trajectory.load(checkpoint);verify(result)
        event=dict(operation=name,status='recovered_checkpoint',checkpoint=str(checkpoint))
    else:
        folders=sorted(p for p in root.glob(name+'_attempt_*') if p.is_dir())
        if len(folders)>=max_attempts:raise RuntimeError('Stage interrupted attempt limit: '+name)
        current=recover(folders[-1],current) if folders and recover else current
        attempt=root/f'{name}_attempt_{len(folders)+1:02d}'
        result,event=execute(current,attempt)
        verify(result);result.save(checkpoint)
    result=Trajectory.load(checkpoint)
    write_json(receipt,dict(event=event,checkpoint=checkpoint.name,attempt=len(list(root.glob(name+'_attempt_*'))),arrays_sha256=sha256(checkpoint/'trajectory.npz'),metadata_sha256=sha256(checkpoint/'trajectory.json')))
    return result,event
