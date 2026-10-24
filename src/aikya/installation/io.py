"""Focused installer io responsibilities."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from aikya.documentation.layout import asset_bytes,stamp,generated
from aikya.installation.defaults import TEMPLATE
from aikya.installation.context import InstallerContext
from aikya.installation.discovery import read_json_safe


def upgrade_exact_markdown_source(root: Path, source: Path | bytes, destination: Path, actions: list[str]) -> bool:
    """Add the footer only to a byte-identical distributed Markdown copy."""
    if destination.suffix.lower()!='.md':return False
    for part in (destination,*destination.parents):
        if part==root.parent:break
        if part.is_symlink():raise ValueError('Symlinked Markdown destination')
    if not destination.resolve().is_relative_to(root.resolve()):raise ValueError('Markdown destination escapes project')
    if not destination.is_file():return False
    raw=source if isinstance(source,bytes) else source.read_bytes()
    rendered=asset_bytes(destination,raw)
    if raw==rendered or destination.read_bytes()!=raw:return False
    backup=root/'.harness/backup-docs-layout/runtime'/destination.relative_to(root)
    for part in (backup,*backup.parents):
        if part==root.parent:break
        if part.is_symlink():raise ValueError('Symlinked Markdown backup')
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copy2(destination,backup)
    destination.write_bytes(rendered)
    actions.append('UPDATED verified Markdown footer '+str(destination))
    return True



def safe_write(path: Path, content: str, actions: list[str], *, replace_managed: bool=False) -> None:
    if path.suffix.lower()=='.md':content=stamp(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if replace_managed and path.is_file() and generated(path.read_text(encoding='utf8')):
            path.write_text(content, encoding='utf8')
            actions.append('UPDATED ' + str(path))
        elif path.is_file() and path.read_text(encoding='utf8') == content:
            actions.append('IGUAL ' + str(path))
        else:
            actions.append('PRESERVED (not overwritten) ' + str(path))
        return
    path.write_text(content, encoding='utf8')
    actions.append('CREATED ' + str(path))



def merge_settings(target: Path, actions: list[str], *, context: InstallerContext=None) -> None:
    context=context or InstallerContext()
    HERE=context.source_root
    TEMPLATE=context.template_root
    from aikya.installation.hook_commands import project_settings
    source = project_settings(read_json_safe(TEMPLATE / '.claude/settings.json'), target)
    path = target / '.claude/settings.json'
    if not path.exists():
        safe_write(path, json.dumps(source, indent=2, ensure_ascii=False)+'\n', actions)
        return
    try:
        local = json.loads(path.read_text(encoding='utf8'))
        if not isinstance(local, dict):
            raise ValueError('settings.json no es objeto JSON')
    except (ValueError, OSError, UnicodeError) as exc:
        safe_write(target / '.harness/settings.harness-proposed.json', json.dumps(source, indent=2)+'\n', actions)
        actions.append(f'NOTICE invalid settings.json: {exc}; left unchanged')
        return
    merged = json.loads(json.dumps(local))
    perms = merged.setdefault('permissions', {})
    if not isinstance(perms, dict):
        actions.append('AVISO permissions existente no es objeto; revisar manualmente')
        return
    for section in ('ask','deny'):
        items = perms.setdefault(section, [])
        if not isinstance(items, list):
            actions.append(f'AVISO permissions.{section} no es lista; revisar manualmente')
            return
        for rule in source['permissions'].get(section, []):
            if rule not in items:
                items.append(rule)
    hooks = merged.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        actions.append('AVISO hooks existente no es objeto; revisar manualmente')
        return
    for event, groups in source['hooks'].items():
        theirs = hooks.setdefault(event, [])
        if not isinstance(theirs, list):
            actions.append(f'AVISO hooks.{event} no es lista; revisar manualmente')
            return
        for group in groups:
            cmd = group['hooks'][0]['command']
            exists = any(isinstance(g, dict) and any(h.get('command') == cmd for h in g.get('hooks', []) if isinstance(h, dict)) for g in theirs)
            if not exists:
                theirs.append(group)
    if merged != local:
        path.write_text(json.dumps(merged, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
        actions.append('FUSIONADO (sin eliminar reglas previas) ' + str(path))
    else:
        actions.append('UNCHANGED ' + str(path))
