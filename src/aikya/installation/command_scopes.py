"""Reuse verified global commands; retire only unchanged selected-project copies."""
import hashlib
from pathlib import Path
from aikya.cli.commands import BOOTSTRAP_COMMANDS
from aikya.documentation.layout import asset_bytes
from aikya.installation.runtime import owned_files, safe_path
from aikya.resource_paths import source_path
from aikya.storage import atomic_write


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def global_commands(source, home=None):
    home = Path(home or Path.home()).expanduser().resolve()
    runtime = home / '.claude/aikya-harnes'
    skills = home / '.claude/skills'
    try:
        if any(p.is_symlink() for p in (runtime, skills, runtime.parent)):
            return None
        recorded = owned_files(runtime)
        for name in ('aikya_cli.py', '_aikya_bootstrap.py', 'src/aikya/__init__.py', 'src/aikya/cli/main.py'):
            path = safe_path(runtime, name)
            if not path.is_file() or digest(path.read_bytes()) != recorded.get(name):
                return None
        for name in BOOTSTRAP_COMMANDS:
            path = safe_path(skills, name + '/SKILL.md')
            original = source_path(source, 'aikya-skills') / name / 'SKILL.md'
            if not path.is_file() or path.read_bytes() != asset_bytes(path, original.read_bytes()):
                return None
        return runtime
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def reconciliation_plan(target, source, global_runtime):
    """No writes. A whole folder must contain only its verified command file."""
    from aikya.installation.registration import verified_skill_upgrade
    target = Path(target).resolve()
    skills = target / '.claude/skills'
    if skills == global_runtime.parent / 'skills':
        return []
    previous = {}
    for root in (target / '.aikya/runtime', target / 'aikya/scripts/harness'):
        safe_path(target, root.relative_to(target))
        previous.update(owned_files(root))
    result = []
    for name in BOOTSTRAP_COMMANDS:
        path = safe_path(skills, name + '/SKILL.md')
        if not path.exists():
            continue
        original = source_path(source, 'aikya-skills') / name / 'SKILL.md'
        raw = path.read_bytes() if path.is_file() else None
        owned = raw is not None and list(path.parent.iterdir()) == [path]
        if owned:
            owned = raw == original.read_bytes() or verified_skill_upgrade(
                path, original, previous.get('aikya-skills/' + name + '/SKILL.md'))
        operation = {'path': path, 'action': 'retire' if owned else 'preserve'}
        if owned:
            backup = safe_path(target, '.harness/command-backups/' + digest(raw) + '/' + name + '/SKILL.md')
            if backup.exists() and (not backup.is_file() or backup.read_bytes() != raw):
                raise ValueError('Conflicting command backup; review before reconciliation: ' + name)
            operation.update(raw=raw, backup=backup,
                             global_path=global_runtime.parent / 'skills' / name / 'SKILL.md',
                             global_raw=(global_runtime.parent / 'skills' / name / 'SKILL.md').read_bytes())
        result.append(operation)
    return result


def reconcile(target, source, global_runtime, logs, *, dry_run=False, operations=None):
    operations = reconciliation_plan(target, source, global_runtime) if operations is None else operations
    # Validate the entire selection again before the first mutation.
    for op in operations:
        if op['action'] == 'retire':
            safe_path(Path(target).resolve(), op['path'].relative_to(Path(target).resolve()))
            safe_path(global_runtime.parent, op['global_path'].relative_to(global_runtime.parent))
            safe_path(Path(target).resolve(), op['backup'].relative_to(Path(target).resolve()))
            if (op['path'].read_bytes() != op['raw'] or list(op['path'].parent.iterdir()) != [op['path']] or
                    op['global_path'].read_bytes() != op['global_raw']):
                raise ValueError('Command changed since reconciliation preview')
    for op in operations:
        if op['action'] == 'preserve':
            logs.append('NEEDS_REVIEW customized local command preserved: ' + str(op['path']))
        elif dry_run:
            logs.append('PLAN retire verified duplicate with backup: ' + str(op['path']))
        else:
            if not op['backup'].exists():
                atomic_write(op['backup'], op['raw'])
            if op['backup'].read_bytes() != op['raw']:
                raise ValueError('Command backup verification failed')
            op['path'].unlink()
            op['path'].parent.rmdir()
            logs.append('RETIRED verified project duplicate; using global command: ' + op['path'].parent.name)
    return operations


def preview_reconciliation(target, source, global_runtime):
    target = Path(target).resolve()
    try:
        operations = {op['path'].parent.name: op for op in reconciliation_plan(target, source, global_runtime)}
        result = []
        for name in BOOTSTRAP_COMMANDS:
            op = operations.get(name)
            row = {'path': '.claude/skills/' + name + '/SKILL.md', 'action': 'REUSE_GLOBAL_COMMAND'}
            if op is not None:
                row['action'] = 'RETIRE_VERIFIED_COMMAND_WITH_BACKUP' if op['action'] == 'retire' else 'BLOCKED'
                if op['action'] == 'preserve':
                    row['reason'] = 'Customized duplicate command requires review; preserved'
                else:
                    result.append({'path': op['backup'].relative_to(target).as_posix(), 'action': 'CREATE_MANAGED'})
            result.append(row)
        return result
    except ValueError as exc:
        return [{'path': '.claude/skills', 'action': 'BLOCKED', 'reason': str(exc)}]
