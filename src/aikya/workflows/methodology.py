"""Canonical methodologies and explicit onboarding choices; no project writes."""
from __future__ import annotations
OPTIONS=('odd','sdd')
INPUTS=('odd','sdd','standard')

def normalize_methodology(value: str | None) -> str:
    if value is None or value=='standard':return 'odd'
    if not isinstance(value,str) or value not in OPTIONS:raise ValueError('Invalid methodology; choose odd or sdd')
    return value

def selection(requested=None,previous=None):
    if requested is not None:chosen=normalize_methodology(requested)
    elif previous is not None:chosen=normalize_methodology(previous)
    else:chosen=None
    if previous=='sdd' and chosen not in (None,'sdd'):
        raise ValueError('Disabling SDD requires a separately reviewed migration')
    return {'methodology':chosen,'methodology_options':list(OPTIONS),
            'methodology_required':chosen is None,'recommended_methodology':'odd'}


def migration_plan(root,previous,selected):
    """Normalize only a known-owned profile and matching saved answers; no writes."""
    import hashlib,json
    from pathlib import Path
    root=Path(root);selected=normalize_methodology(selected)
    if previous.get('_generated_by')!='claude-dev-harness-interactive':return []
    decisions=previous.get('decisions',{})
    if not isinstance(decisions,dict):raise ValueError('Invalid managed profile')
    if decisions.get('methodology')==selected:return []
    result=[]
    for name,backup_name in (('.harness/project-profile.json','project-profile.json'),('.aikya/answers.json','answers.json')):
        file=root/name;backup=root/'.harness/backup-odd'/backup_name
        for path in (file,backup):
            if any(p.is_symlink() for p in (path,*path.parents) if p==root or root in p.parents):raise ValueError('Unsafe methodology migration path')
        if not file.is_file():continue
        raw=file.read_bytes();value=json.loads(raw);data=value.get('decisions',value) if isinstance(value,dict) else None
        if not isinstance(data,dict):raise ValueError('Review saved answers before methodology migration')
        if name.endswith('answers.json'):
            identifiers=[k for k in ('project_type','mode') if k in data]
            if not identifiers or any(decisions.get(k)!=data[k] for k in identifiers) or normalize_methodology(data.get('methodology'))!=normalize_methodology(decisions.get('methodology')):raise ValueError('Saved answers belong to a different profile/methodology; reconcile before migration')
        updated=json.loads(json.dumps(value));updated.get('decisions',updated)['methodology']=selected
        result.append({'path':name,'backup':backup.relative_to(root).as_posix(),'action':'UPDATE_MANAGED_METHODOLOGY_WITH_BACKUP','expected_sha256':hashlib.sha256(raw).hexdigest(),'updated':updated})
    return result

def apply_migration(root,operations):
    import hashlib,shutil
    from pathlib import Path
    from aikya.core.state import atomic
    root=Path(root)
    for op in operations:
        file=root/op['path'];backup=root/op['backup']
        if hashlib.sha256(file.read_bytes()).hexdigest()!=op['expected_sha256']:raise ValueError('Methodology source changed since preview')
        if any(p.is_symlink() for p in (backup,*backup.parents) if p==root or root in p.parents):raise ValueError('Unsafe methodology backup')
    for op in operations:
        file=root/op['path'];backup=root/op['backup'];backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(file,backup)
        atomic(file,op['updated'])
