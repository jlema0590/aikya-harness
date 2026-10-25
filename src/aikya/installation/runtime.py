"""Preflight coupled runtime upgrades, retain backups and restore failed copies."""
import hashlib
import json
from pathlib import Path
from aikya.documentation.layout import asset_bytes
from aikya.installation.assets import runtime_assets,runtime_asset_bytes
from aikya.resource_paths import source_path
from aikya.storage import atomic_write


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe runtime path')
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents) if p == root or root in p.parents):
        raise ValueError('Symlinked runtime path: ' + str(path))
    return path


def owned_files(root):
    result = {}
    for name in ('manifest.json', '.bundle-manifest.json'):
        path = safe_path(root, name)
        if not path.exists():
            continue
        if not path.is_file() or path.stat().st_size > 3_000_000:
            raise ValueError('Invalid runtime ownership manifest')
        data = json.loads(path.read_text(encoding='utf8')).get('files')
        if not isinstance(data, dict):
            raise ValueError('Invalid runtime ownership manifest')
        result.update(data)
    return result


def prepare_bundle(runtime, source, kind, *, methodology=None):
    runtime = Path(runtime)
    previous = owned_files(runtime)
    predecessors = json.loads(source_path(source, 'migrations/structure-predecessors.json').read_text())
    from aikya.documentation.migration_hashes import ASSETS
    from aikya.workflows.sdd.assets import TRUSTED
    operations = []
    for asset in runtime_assets(source, kind, methodology=methodology):
        name = asset.destination.as_posix()
        destination = safe_path(runtime, name)
        if destination.exists() and not destination.is_file():
            raise ValueError('Non-regular runtime destination: ' + name)
        old = destination.read_bytes() if destination.exists() else None
        new = runtime_asset_bytes(asset.destination, asset.read_bytes())
        if old == new:
            action = 'KEEP'
        elif old is None:
            action = 'CREATE'
        else:
            record = ASSETS.get('aikya/scripts/harness/' + name, {})
            trusted = set(predecessors.get(name, [])) | set(record.get('variants', {})) | set(TRUSTED.get('aikya/scripts/harness/' + name, []))
            trusted.update(x for x in (previous.get(name), record.get('sha256')) if isinstance(x, str))
            if digest(old) in trusted or old == asset.read_bytes():
                action = 'UPDATE'
            elif asset.kind == 'package' or name in ('_aikya_bootstrap.py','aikya_cli.py','install.py','aikya_setup.py','agent_runtime.py') or name.startswith(('aikya-template/', 'sdd-templates/', 'compatibility/')):
                raise ValueError('Customized coupled runtime requires review before upgrade: ' + name)
            else:
                action = 'PRESERVE'
        backup = safe_path(runtime, Path('package-backups') / digest(old) / name) if action == 'UPDATE' else None
        if backup is not None and backup.exists() and (not backup.is_file() or backup.read_bytes() != old):
            raise ValueError('Conflicting runtime package backup: ' + name)
        legacy_backup = None
        if action == 'UPDATE' and kind == 'initialized':
            if asset.destination.suffix == '.md' and old == asset.read_bytes() and old != new:
                legacy_backup = safe_path(runtime.parents[2], '.harness/backup-docs-layout/runtime/aikya/scripts/harness/' + name)
            if name == 'aikya_requirements.py' and digest(old) in predecessors.get('v56_aikya_requirements.py', []):
                legacy_backup = safe_path(runtime.parents[2], '.harness/backup-v56/aikya_requirements.py')
            if legacy_backup is not None and legacy_backup.exists() and legacy_backup.read_bytes() != old:
                raise ValueError('Conflicting legacy runtime backup')
        operations.append({'path': destination, 'relative': name, 'source': asset, 'source_hash': asset.source_digest(), 'kind': asset.kind, 'old': old, 'new': new, 'backup': backup, 'legacy_backup': legacy_backup, 'action': action})
    operations.extend(retired_template_assets(runtime, source, previous))
    return operations


def retired_template_assets(runtime, source, previous):
    """Remove the old catalog only when its exact bytes have known provenance."""
    records = json.loads(source_path(source, 'migrations/template-path-predecessors.json').read_text())['files']
    legacy = safe_path(runtime, 'documentation-templates')
    if not legacy.exists():
        return []
    operations = []
    for path in sorted(legacy.rglob('*')):
        name = path.relative_to(runtime).as_posix()
        safe_path(runtime, name)
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError('Non-regular legacy template asset: ' + name)
        raw = path.read_bytes()
        trusted = set(records.get(name, []))
        if isinstance(previous.get(name), str):
            trusted.add(previous[name])
        if digest(raw) not in trusted:
            raise ValueError('Customized legacy template asset requires review: ' + name)
        backup = safe_path(runtime, Path('package-backups') / digest(raw) / name)
        if backup.exists() and (not backup.is_file() or backup.read_bytes() != raw):
            raise ValueError('Conflicting runtime package backup: ' + name)
        operations.append({'path': path, 'relative': name, 'source': None, 'source_hash': None,
                           'kind': 'retired', 'old': raw, 'new': None, 'backup': backup,
                           'legacy_backup': None, 'action': 'RETIRE'})
    return operations


def apply_bundle(runtime, operations, actions):
    runtime = Path(runtime)
    # Revalidate the complete batch before activating any new adapter.
    for op in operations:
        path = safe_path(runtime, op['relative'])
        if (path.read_bytes() if path.exists() else None) not in (op['old'],op['new']) or (op['source'] is not None and op['source'].source_digest() != op['source_hash']):
            raise ValueError('Runtime changed after package preflight: ' + op['relative'])
    changed = []
    try:
        for op in sorted(operations, key=lambda op: op['kind'] == 'adapter'):
            if op['action'] not in ('CREATE', 'UPDATE', 'RETIRE'):
                continue
            if op['backup'] is not None and not op['backup'].exists():
                atomic_write(op['backup'], op['old'])
            if op['legacy_backup'] is not None and not op['legacy_backup'].exists():
                atomic_write(op['legacy_backup'], op['old'])
            if op['action'] == 'RETIRE':
                op['path'].unlink()
            else:
                atomic_write(op['path'], op['new'])
            changed.append(op)
        manifest = {op['relative']: digest(op['new']) for op in operations if op['action'] not in ('PRESERVE', 'RETIRE')}
        atomic_write(safe_path(runtime, '.bundle-manifest.json'), json.dumps({'schema': 1, 'files': manifest}, indent=2) + '\n')
    except BaseException:
        for op in reversed(changed):
            if op['old'] is None:
                op['path'].unlink(missing_ok=True)
            else:
                atomic_write(op['path'], op['old'])
        raise
    actions.extend(op['action'] + ' runtime asset: ' + op['relative'] for op in operations if op['action'] != 'KEEP')
    if any(op['action'] == 'RETIRE' for op in operations):
        legacy = safe_path(runtime, 'documentation-templates')
        for directory in sorted(legacy.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if directory.is_dir() and not directory.is_symlink():
                directory.rmdir()
        legacy.rmdir()
