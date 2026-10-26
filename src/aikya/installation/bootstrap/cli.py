"""Clean install/update/doctor/uninstall, callable before Aikya is installed."""
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import uuid
from . import download, environment, state, launchers, settings


from .options import parser

def locations(scope, target, commands=()):
    base = Path.home().resolve() if scope == 'global' else target
    runtime = base / '.claude/aikya-harnes' if scope == 'global' else base / '.aikya/runtime'
    return [runtime, *(base / '.claude/skills' / name / 'SKILL.md' for name in commands), base / '.claude/settings.json', base / '.claude/visibility-proposed.json'] + ([base / '.aikya/bootstrap.json', base / '.aikya/visibility-proposed.json'] if scope == 'project' else [])


def registration(python, scope, target, dry_run=False):
    code = ('from pathlib import Path;import sys;from aikya.resource_paths import source_root;'
            'from aikya.installation.registration import setup;'
            'print("\\n".join(setup(source_root(),Path(sys.argv[2]),sys.argv[1],dry_run=sys.argv[3]=="1")))')
    return environment.run(python, '-c', code, scope, target or Path.cwd(), '1' if dry_run else '0')


def install_harness(args, root, receipt_file, locked=False):
    args.version = download.resolve_version(args.version, args.offline_dir)
    environment.check_python(args.python)
    old = json.loads(receipt_file.read_text(encoding='utf8')) if receipt_file.exists() else None
    owned_locations = locations(args.scope, args.target)
    state.snapshot(owned_locations)  # Validate every managed path before provisioning.
    if owned_locations[0].exists() and old is None:
        raise ValueError('Existing runtime has no clean-installer receipt; review adoption explicitly')
    if args.dry_run:
        print(json.dumps({'action': args.action, 'version': args.version, 'scope': args.scope, 'target': str(args.target), 'root': str(root), 'writes': False}))
        return 0
    with tempfile.TemporaryDirectory(prefix='aikya-release-') as temporary:
        assets = download.fetch_release(args.version, Path(temporary), args.offline_dir)
        wheel = assets['wheel']; environment.verify_wheel(wheel, args.version)
        with nullcontext() if locked else state.installation_lock(root):
            if (root / 'pending.json').exists():
                raise ValueError('Interrupted operation needs review; run aikya-manage doctor')
            old = json.loads(receipt_file.read_text(encoding='utf8')) if receipt_file.exists() else None
            candidate = root / 'versions' / args.version / uuid.uuid4().hex
            python = environment.create_environment(candidate, args.python, wheel)
            registration(python, args.scope, args.target, True)
            commands = json.loads(environment.run(python, '-c', 'import json;from aikya.cli.commands import BOOTSTRAP_COMMANDS;print(json.dumps(list(BOOTSTRAP_COMMANDS)))'))
            owned_locations = locations(args.scope, args.target, commands)
            managed = [*owned_locations, root / 'bin']
            before = state.snapshot(managed)
            configuration_file = str((Path.home().resolve() if args.scope == 'global' else args.target) / '.claude/settings.json')
            metadata = [receipt_file, root / 'current.json', root / 'launchers.json']
            metadata_before = state.snapshot(metadata)
            pending = root / 'pending.json'
            state.write_json(pending, {'before_hashes': {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in before.items()}, 'environment': str(candidate), 'scope': args.scope, 'target': str(args.target)})
            try:
                if old:
                    settings.remove(old.get('settings_changes', []), owned_locations[0])
                settings_before = state.snapshot([Path(configuration_file)])
                print(registration(python, args.scope, args.target))
                launchers.publish(root, candidate)
                complete_after = state.snapshot(owned_locations)
                settings_changes = settings.changes(settings_before, {name: raw for name, raw in complete_after.items() if name == configuration_file})
                after = {name: raw for name, raw in complete_after.items() if name != configuration_file and (raw != before.get(name) or name in (old or {}).get('after', {}))}
                original = {name: raw for name, raw in before.items() if name in after}
                if old:
                    original.update({name: raw for name, raw in old['before'].items() if name in after})
                    for name in old['after']:
                        if name not in old['before']:
                            original.pop(name, None)
                receipt = {'schema': 1, 'version': args.version, 'environment': str(candidate), 'python': str(python),
                           'scope': args.scope, 'target': str(args.target) if args.target else None,
                           'source': download.REPOSITORY + '/releases/download/v' + args.version,
                           'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
                           'before': original, 'after': after, 'commands': commands, 'settings_changes': settings_changes}
                state.write_json(receipt_file, receipt)
                state.activate(root, {key: receipt[key] for key in ('version', 'environment', 'python')})
                pending.unlink()
            except BaseException:
                preserved = state.restore({**before, **metadata_before}, {**state.snapshot(managed), **state.snapshot(metadata)})
                if not preserved:
                    pending.unlink(missing_ok=True)
                raise
    print('Installed ' + args.version + '; executable directory: ' + str(root / 'bin'))
    return 0


def uninstall_harness(args, root, receipt_file, locked=False):
    if not receipt_file.is_file():
        raise ValueError('No owned installation receipt for this scope/target')
    receipt = json.loads(receipt_file.read_text(encoding='utf8'))
    allowed = [*locations(args.scope, args.target, receipt.get('commands', [])), root / 'bin']
    for name in set(receipt['before']) | set(receipt['after']):
        path = Path(name)
        if not any(path == base or (base.suffix != '.json' and path.is_relative_to(base)) for base in allowed):
            raise ValueError('Receipt contains an unowned path')
    if args.dry_run:
        print('PLAN: remove only unchanged owned registration assets; preserve project documents')
        return 0
    with nullcontext() if locked else state.installation_lock(root):
        if (root / 'pending.json').exists():
            raise ValueError('Interrupted operation requires recovery before uninstall')
        for record in receipt.get('settings_changes', []):
            if Path(record['path']) != (Path.home().resolve() if args.scope == 'global' else args.target) / '.claude/settings.json':
                raise ValueError('Unowned settings change record')
        settings.remove(receipt.get('settings_changes', []), allowed[0])
        other_receipts = [p for p in (root / 'receipts').glob('*.json') if p != receipt_file]
        after = {name: raw for name, raw in receipt['after'].items() if not other_receipts or not Path(name).is_relative_to(root / 'bin')}
        before = {name: raw for name, raw in receipt['before'].items() if name in after}
        preserved = state.restore(before, after)
        if preserved:
            print(json.dumps({'preserved': preserved, 'environment_retained': True}))
            return 2
        if not other_receipts:
            preserved = launchers.remove(root)
            if preserved:
                print(json.dumps({'preserved_launchers': preserved, 'environment_retained': True}))
                return 2
        receipt_file.unlink()
        if not other_receipts:
            (root / 'current.json').unlink(missing_ok=True)
            # Windows may retain running executables; record cleanup instead of forced removal.
            try:
                if state.active_references(root):
                    print('Retained environments referenced by initialized projects.')
                else:
                    shutil.rmtree(root / 'versions')
            except OSError:
                state.write_json(root / 'cleanup-pending.json', {'path': str(root / 'versions')})
        print('Removed unchanged owned registration assets; project documents preserved')
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf8')
    args = parser().parse_args(argv)
    try:
        root = environment.app_root(); state.safe(root)
        if args.action == 'doctor':
            from .coordinator import component_status
            statuses = component_status(root)
            print(json.dumps({'components': statuses, 'root': str(root), 'installed': (root / 'current.json').is_file(),
                              'pending': (root / 'pending.json').exists(), 'cleanup_pending': (root / 'cleanup-pending.json').exists(),
                              'project_references': state.active_references(root),
                              'flow_connection': {'mode': 'session', 'status': 'not-checked', 'command': '/aikya-flow connect <cache-root>'}}))
            return 2 if (root / 'pending.json').exists() or any(p.get('status') == 'partial' for p in statuses) else 0
        if args.scope == 'project':
            if args.target is None or not args.target.is_dir():
                raise ValueError('Project scope requires --target pointing to an existing directory')
            args.target = args.target.expanduser().absolute(); state.safe(args.target)
        receipt_file = state.safe(state.receipt_path(root, args.scope, args.target))
        from .coordinator import execute
        return execute(args, root, receipt_file)
    except (ValueError, OSError, RuntimeError, TimeoutError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2
