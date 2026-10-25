"""Focused installer migrations responsibilities."""
from __future__ import annotations
from aikya.resource_paths import source_path
from aikya.installation.assets import resolve_runtime_asset
import hashlib
import json
import shutil
from pathlib import Path
from aikya.documentation.layout import asset_bytes
from aikya.installation.defaults import HERE,TEMPLATE
from aikya.installation.context import InstallerContext
from aikya.installation.discovery import read_json_safe,relative


def copy_legacy_docs(target: Path, actions: list[str]) -> None:
    """Import substantive legacy docs into canonical paths; preserve originals."""
    from aikya.documentation.layout import canonical, write_document, safe, substantive, ABSORB, RETIRE, append_section, remap_links
    source_dir=target/'docs'
    if not source_dir.is_dir() or source_dir.is_symlink():return
    for old in sorted(source_dir.rglob('*.md')):
        if not old.is_file() or any(p.is_symlink() for p in (old,*old.parents) if p==target or target in p.parents):continue
        relative=old.relative_to(source_dir).as_posix()
        body=old.read_text(encoding='utf8')
        if not substantive(body) or relative in RETIRE:continue
        if relative.startswith('harness/') and relative not in ABSORB and relative!='harness/token-policy.md':
            actions.append('PRESERVED unrecognized legacy document: '+str(old));continue
        if relative in ABSORB:
            try:append_section(target,'overview.md','Legacy '+old.stem,remap_links(body,relative,'overview.md',asset_prefix='../../docs'))
            except ValueError:actions.append('PRESERVED conflicting legacy document: '+str(old))
            continue
        new=safe(target,canonical(relative))
        if new.exists():
            actions.append('PRESERVED unmigrated legacy file: '+str(old));continue
        write_document(target,relative,remap_links(body,relative,canonical(relative),asset_prefix='../../docs'),index=False)
        actions.append('COPIED canonical legacy docs (original preserved): '+str(new))



def managed_path_conflicts(target: Path) -> list[dict]:
    """Reject symbolic links, including dangling links, before managed writes."""
    import os
    conflicts=[]
    for name in ('.claude','.aikya','.harness','aikya','CLAUDE.md','harness.json'):
        base=target/name
        if base.is_symlink():
            conflicts.append({'path':name,'action':'BLOCKED','reason':'Symlinked managed path'});continue
        if not base.is_dir():continue
        for folder,dirs,files in os.walk(base,followlinks=False):
            for entry in dirs+files:
                path=Path(folder)/entry
                if path.is_symlink():conflicts.append({'path':path.relative_to(target).as_posix(),'action':'BLOCKED','reason':'Symlinked managed path'})
    return conflicts



def documentation_runtime_plan(target: Path, *, context: InstallerContext=None) -> list[dict]:
    context=context or InstallerContext()
    HERE=context.source_root
    TEMPLATE=context.template_root
    """Read-only known-hash update and backup preview."""
    from aikya.documentation.migration_hashes import ASSETS
    from aikya.installation.signatures import predecessor_hashes
    coupled_templates={'documentation_templates.py','documentation_workflows.py',
                       'sdd_templates.py','claude_templates.py','doc_bootstrap.py',
                       'aikya-template/manifest.json'}
    from aikya.installation.registration import EXECUTION_FILES
    coupled_templates.update(EXECUTION_FILES+('methodology.py','aikya_cli.py','aikya_analyze.py','aikya_setup.py','install.py','token_report.py','sdd_engine.py'))
    operations=[]
    for relative,record in ASSETS.items():
        if relative=='CLAUDE.md':continue  # Existing repository instructions stay owner-controlled.
        destination=target/relative;source=resolve_runtime_asset(HERE,record['source'])
        if source.source is not None and not source.source.is_file():continue
        if any(p.is_symlink() for p in (destination,*destination.parents) if p==target or target in p.parents):
            operations.append({'path':relative,'action':'BLOCKED','reason':'Symlinked runtime asset'});continue
        if not destination.is_file():continue
        raw=destination.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        suffix=record.get('variants',{}).get(digest,'')
        expected=asset_bytes(relative,source.read_bytes(),suffix=suffix)
        if raw==expected:continue
        if digest!=record['sha256'] and digest not in record.get('variants',{}) and digest not in predecessor_hashes(HERE,record['source']):
            if record['source'] in coupled_templates or record['source'].startswith('sdd-templates/'):
                operations.append({'path':relative,'action':'BLOCKED',
                                   'reason':'Customized template asset requires review before updating its coupled runtime/catalog'})
            continue
        backup=target/'.harness/backup-docs-layout/runtime'/relative
        if any(p.is_symlink() for p in (backup,*backup.parents) if p==target or target in p.parents):
            operations.append({'path':relative,'action':'BLOCKED','reason':'Symlinked runtime backup'});continue
        operations.append({'path':relative,'source':record['source'],'action':'UPDATE_VERIFIED_RUNTIME','backup':backup.relative_to(target).as_posix(),'suffix':suffix})
    return operations



def upgrade_documentation_runtime(target: Path, actions: list[str], *, context: InstallerContext=None) -> None:
    context=context or InstallerContext()
    HERE=context.source_root
    TEMPLATE=context.template_root
    """Upgrade only byte-identical baseline assets, retaining local backups."""
    operations=documentation_runtime_plan(target, context=context)
    if any(op['action']=='BLOCKED' for op in operations):raise ValueError('Unsafe runtime update: '+json.dumps(operations))
    for op in operations:
        destination=target/op['path'];source=resolve_runtime_asset(HERE,op['source']);backup=target/op['backup']
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(destination,backup)
        destination.write_bytes(asset_bytes(destination,source.read_bytes(),suffix=op.get('suffix','')))
        actions.append('UPDATED verified baseline runtime: '+op['path'])



def migrate_v55_project_config(target: Path, actions: list[str], *, context: InstallerContext=None) -> None:
    context=context or InstallerContext()
    HERE=context.source_root
    TEMPLATE=context.template_root
    """Actualizar exclusivamente hooks anteriores bit a bit y quality gates de Aikya."""
    for name in ('request_docs.py','stop_docs.py','skills_ready.py'):
        old=source_path(HERE,'migrations/v55/hooks')/name
        newer=TEMPLATE/'.claude/hooks'/name
        current=target/'.claude/hooks'/name
        if (old.is_file() and newer.is_file() and current.is_file()
                and not current.is_symlink() and current.read_bytes()==old.read_bytes()):
            shutil.copy2(newer,current)
            actions.append('UPDATED LEGACY AIKYA HOOK '+str(current))
    config=target/'harness.json'
    if config.is_symlink() or not config.is_file():
        return
    obj=read_json_safe(config)
    if obj.get('schema_version')!=2 or not isinstance(obj.get('checks'),list):
        return
    expected={
        'docs:structure': (['python3','scripts/harness/docs_guard.py','base'],
                           ['python3','aikya/scripts/harness/docs_guard.py','base']),
        'skills:format': (['python3','scripts/harness/skills_lint.py'],
                          ['python3','aikya/scripts/harness/skills_lint.py'])
    }
    changed=False
    for item in obj['checks']:
        if not isinstance(item,dict):
            continue
        update=expected.get(item.get('name'))
        if update and item.get('command')==update[0]:
            item['command']=update[1]
            changed=True
    if changed:
        config.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        actions.append('MIGRADOS quality gates anteriores sin alterar checks personalizados.')
