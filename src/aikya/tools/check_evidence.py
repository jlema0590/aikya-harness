"""Conservative evidence reuse for explicitly declared deterministic local checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
from aikya.core.checkpoints import identity, safe_file, fingerprint
from aikya.code_index.policy import excluded, read_source


def binding(root, check):
    # A command that depends on external services/unknown state is never reusable.
    if check.get('reusable') is not True:return None
    root=Path(root).resolve();files={};total=0
    try:
        for base,dirs,names in os.walk(root,followlinks=False):
            dirs[:]=sorted(d for d in dirs if not excluded((Path(base)/d).relative_to(root).as_posix()))
            for name in sorted(names):
                path=Path(base)/name;relative=path.relative_to(root).as_posix()
                if excluded(relative):continue
                raw=read_source(root,relative,1_048_576);total+=len(raw)
                if len(files)>=12000 or total>100_000_000:return None
                files[relative]=hashlib.sha256(raw).hexdigest()
        command=check.get('command')
        if not isinstance(command,list) or not command:return None
        executable=shutil.which(command[0])
        if not executable:return None
        executable_hash=fingerprint(Path(executable).resolve())
        record={'identity':identity(root),'files':files,'check':check,'executable':executable_hash,
                'environment':dict(os.environ)}
        return hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
    except (ValueError,OSError,TypeError):return None


def reusable(evidence, candidate_binding):
    return bool(candidate_binding and evidence.get('binding')==candidate_binding and
                evidence.get('kind')=='process' and type(evidence.get('exit_code')) is int and evidence['exit_code']==0)


def previous(root):
    from aikya.core.state import read_active
    context={'root':str(root),'session_id':os.environ.get('CLAUDE_SESSION_ID','local')}
    try:
        active=read_active(context) or {}
        return [item for event in active.get('history',[]) for item in event.get('evidence',[])]
    except (ValueError,OSError):return []
