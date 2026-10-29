"""Shared installer options and side-effect-free entry previews (stdlib only)."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys

def parser():
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest='action', required=True)
    for action in ('install', 'update', 'uninstall', 'doctor'):
        command = sub.add_parser(action)
        if action in ('install', 'update'):
            command.add_argument('--code-index', choices=('none','dart','all'), default=None)
            command.add_argument('--version', help='Release X.Y.Z; defaults to the latest published stable release')
            command.add_argument('--python', type=Path, default=Path(sys.executable))
            command.add_argument('--offline-dir', type=Path)
            selection = command.add_mutually_exclusive_group()
            selection.add_argument('--mods', choices=('recommended', 'all', 'none'))
            selection.add_argument('--mod', action='append')
            command.add_argument('--mods-version')
            command.add_argument('--no-path', action='store_true')
        if action != 'doctor':
            command.add_argument('--scope', choices=('global', 'project'), default='global')
            command.add_argument('--target', type=Path)
            command.add_argument('--dry-run', action='store_true')
    sub.choices['uninstall'].add_argument('--keep-mods', action='store_true')
    return result


RECOMMENDED = ('aikya-flow', 'aikya-usage')


@dataclass(frozen=True)
class ComponentPlan:
    selected: tuple
    scope: str
    target: str | None
    explicit: bool


def plan_components(scope, target, selection, previous_receipt, action='install'):
    previous = (previous_receipt or {}).get('selected', [])
    if selection is None:
        selected = previous if previous_receipt is not None or action == 'update' else RECOMMENDED
    elif selection == 'none':
        selected = ()
    elif selection == 'recommended':
        selected = RECOMMENDED
    elif selection == 'all':
        selected = ('*',)
    else:
        selected = selection
        if isinstance(selected, str):raise ValueError('Unknown Mods selection')
    selected = tuple(sorted(set(selected)))
    if any(name != '*' and not re.fullmatch(r'aikya-[a-z0-9-]+', name) for name in selected):
        raise ValueError('Invalid Mods selection')
    return ComponentPlan(selected, 'user' if scope == 'global' else 'project', str(target) if target else None, selection is not None)


def app_root():
    override = os.environ.get('AIKYA_INSTALL_ROOT')
    if override:
        return Path(override).expanduser().absolute()
    home = Path.home().resolve()
    if sys.platform == 'win32':
        return Path((os.environ.get('LOCALAPPDATA') or str(home / 'AppData/Local'))) / 'Aikya'
    if sys.platform == 'darwin':
        return home / 'Library/Application Support/Aikya'
    if sys.platform.startswith('linux'):
        return Path((os.environ.get('XDG_DATA_HOME') or str(home / '.local/share'))) / 'aikya'
    raise ValueError('Supported installation hosts: Windows, Linux and macOS')


def receipt_path(root, scope, target):
    identity = scope + ':' + (str(target) if scope == 'project' else str(Path.home().resolve()))
    return root / 'receipts' / (hashlib.sha256(identity.encode('utf8')).hexdigest() + '.json')


MIN_UNIFIED_VERSION = (7, 1, 0)


def validate_component_version(version, selected, previous):
    if version in (None, 'latest'):return
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Select an explicit numeric Harness release version')
    managed = selected or (previous or {}).get('marketplace_owned')
    if managed and tuple(map(int,version.split('.'))) < MIN_UNIFIED_VERSION:
        raise ValueError('Unified Mods management requires Harness 7.1.0 or newer; older releases support --mods none only without managed Mods')


def preview(args, root, previous, previous_harness=None):
    if args.offline_dir:
        if not args.version or args.version == 'latest':
            raise ValueError('Offline installation requires --version X.Y.Z')
    selection = args.mods if args.mods is not None else args.mod
    plan = plan_components(args.scope,args.target,selection,previous,args.action)
    validate_component_version(args.version,plan.selected,previous)
    if args.offline_dir and plan.selected and (not args.mods_version or args.mods_version == 'latest'):
        raise ValueError('Offline Mods installation requires --mods-version X.Y.Z')
    index_selection=getattr(args,'code_index',None)
    if index_selection is None:index_selection=(previous_harness or {}).get('code_index','none') if args.action=='update' else 'none'
    if index_selection not in ('none','dart','all'):raise ValueError('Invalid stored parser selection')
    return {'action':args.action,'version':args.version or 'latest',
            'mods_version':(args.mods_version or 'latest') if plan.selected else None,
            'mods':list(plan.selected),'scope':args.scope,'target':str(args.target) if args.target else None,
            'root':str(root),'code_index':index_selection,'writes':False,'network':False}


def entry_preview(argv=None):
    args = parser().parse_args(['install',*(argv if argv is not None else sys.argv[1:])])
    try:
        if args.scope == 'project':
            if args.target is None or not args.target.is_dir():raise ValueError('Project scope requires --target pointing to an existing directory')
            args.target=args.target.expanduser().absolute()
        root=app_root();record=root/'components'/receipt_path(root,args.scope,args.target).name
        previous=json.loads(record.read_text(encoding='utf8')) if record.is_file() else None
        harness=receipt_path(root,args.scope,args.target)
        previous_harness=json.loads(harness.read_text()) if harness.is_file() else None
        print(json.dumps(preview(args,root,previous,previous_harness)))
    except (ValueError,OSError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2
    return 0
