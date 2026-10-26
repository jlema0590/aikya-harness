"""Existing SDK file scope and settings approval policy."""
import json
from pathlib import Path
from aikya.core.checkpoints import safe_file

def settings_paths(root):
    root=Path(root)
    return (Path.home()/'.claude/settings.json',root/'.claude/settings.json',root/'.claude/settings.local.json')


def settings_fingerprints(root):
    from aikya.core.checkpoints import fingerprint
    result={}
    for path in settings_paths(root):
        if path.is_symlink():raise ValueError('Symlinked runtime settings')
        result[str(path)]=fingerprint(path)
    return result


def tool_path(request,value):
    root=Path(request['root']).absolute()
    if not Path(value).is_absolute():return value
    try:return Path(value).relative_to(root).as_posix()
    except ValueError:return Path(value).relative_to(root.resolve()).as_posix()


def tool_allowed(request,tool,tool_input):
    if tool not in ('Read','Edit','Write') or not isinstance(tool_input,dict):return False
    if request.get('phase')!='implement' and tool!='Read':return False
    value=tool_input.get('file_path')
    if not isinstance(value,str):return False
    root=Path(request['root']).absolute()
    try:
        relative=tool_path(request,value)
        safe_file(root,relative,write=tool!='Read')
    except (ValueError,OSError):return False
    return relative in request['files'] or (tool=='Read' and relative in request.get('context_files',[]))


def settings_approved(root,config):
    for path in settings_paths(root):
        if not path.exists():continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:raise ValueError('Invalid SDK settings source')
        value=json.loads(path.read_text())
        if not isinstance(value,dict):raise ValueError('Invalid SDK settings source')
        if value.get('hooks') and not config['hooks_approved']:raise ValueError('Configured hooks require explicit review with hooks_approved=true')
