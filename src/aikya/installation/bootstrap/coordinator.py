"""Prepare verified distributions before serializing activation and plugin changes."""
import json
from dataclasses import replace
from pathlib import Path
import tempfile
from . import components, download, environment, mods, state
from .claude_plugins import Claude


def component_status(root):
    return [json.loads(state.safe(p).read_text(encoding='utf8')) for p in sorted((root/'components').glob('*.json'))]


def managed_sources(root):
    return {p['source'] for p in component_status(root) if p.get('marketplace_owned') and p.get('source')}


def execute(args, root, receipt_file):
    component_file = state.safe(root/'components'/receipt_file.name)
    previous = json.loads(component_file.read_text(encoding='utf8')) if component_file.exists() else None
    if previous is not None:components.validate_receipt(previous,args.scope,args.target)
    if args.action == 'uninstall':
        return remove(args, root, receipt_file, component_file, previous)
    selection = args.mods if args.mods is not None else args.mod
    plan = components.plan_components(args.scope,args.target,selection,previous,args.action)
    if args.offline_dir:
        download.resolve_version(args.version,args.offline_dir)
        if plan.selected:mods.resolve_version(args.mods_version,args.offline_dir)
    if args.dry_run:
        from .options import preview
        previous_harness=json.loads(receipt_file.read_text()) if receipt_file.exists() else None
        print(json.dumps(preview(args,root,previous,previous_harness)))
        return 0
    adapter = Claude(args.target) if plan.selected else None
    if adapter:adapter.preflight()
    version = download.resolve_version(args.version,args.offline_dir)
    from .options import validate_component_version
    validate_component_version(version,plan.selected,previous)
    environment.check_python(args.python)
    # TemporaryDirectory may live behind /var on macOS; canonicalize owned paths.
    with tempfile.TemporaryDirectory(prefix='aikya-components-') as temporary:
        stage = Path(temporary).resolve()
        wheel = download.fetch_release(version,stage/'harness',args.offline_dir)['wheel']
        from . import code_index
        previous_harness = json.loads(receipt_file.read_text()) if receipt_file.exists() else None
        selected_index = code_index.selection(getattr(args, 'code_index', None), previous_harness, args.action)
        parser_wheels = code_index.prepare(selected_index, version, stage/'harness', args.offline_dir)
        args.code_index = selected_index
        environment.verify_wheel(wheel,version)
        bundle = None
        if adapter:
            mods_version = mods.resolve_version(args.mods_version,args.offline_dir)
            bundle = mods.prepare_mods(mods_version,stage/'mods',args.offline_dir)
            adapter.preflight(bundle.claude_version)
            components.check_source(replace(bundle,path=mods.storage_root()/"releases"/("v"+mods_version)/"aikya-mods"),previous or {},adapter,managed_sources(root))
            if plan.selected != ('*',) and any(name not in bundle.plugins for name in plan.selected):
                raise ValueError('Selected mod is missing from the verified catalog')
        # Core's established wheel verifier reads from this private staged manifest.
        from . import cli
        args.version=version; args.offline_dir=stage/'harness'
        import hashlib
        (stage/'harness/SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in [wheel, *parser_wheels]))
        with state.installation_lock(root):
            current = json.loads(component_file.read_text(encoding='utf8')) if component_file.exists() else None
            current_harness=json.loads(receipt_file.read_text()) if receipt_file.exists() else None
            if current_harness != previous_harness:raise ValueError('Harness parser selection changed during preparation; retry')
            if current != previous:
                raise ValueError('Component selection changed during preparation; retry')
            if bundle:
                bundle = mods.persist_bundle(bundle,mods.storage_root()/'releases')
                components.check_source(bundle,previous or {},adapter,managed_sources(root))
            cli.install_harness(args,root,receipt_file,locked=True)
            if bundle:
                record = previous or {}
                components.install_plugins(bundle,plan,record,adapter,lambda:state.write_json(component_file,record),managed_sources(root))
            elif previous is None:
                state.write_json(component_file,{'schema':1,'scope':plan.scope,'target':plan.target,'selected':[],'plugins':{},'status':'complete'})
            from . import user_path
            if not args.no_path:
                user_path.ensure_user_path(root/'bin',root=root)
    print('Installation complete. Open a new terminal/Claude session to load PATH and plugins.')
    return 0


def remove(args,root,receipt_file,component_file,previous):
    if args.dry_run:
        print('PLAN: remove unchanged owned Harness assets; preserve user files and unowned plugins')
        return 0
    adapter = None
    if previous and (previous.get('plugins') or previous.get('marketplace_owned')) and not args.keep_mods:
        adapter=Claude(args.target);adapter.preflight()
    from . import cli, user_path
    with state.installation_lock(root):
        current = json.loads(component_file.read_text(encoding='utf8')) if component_file.exists() else None
        if current != previous:raise ValueError('Component receipt changed during uninstall preflight; retry')
        if adapter:
            components.uninstall_plugins(previous,adapter,lambda:state.write_json(component_file,previous))
        result=cli.uninstall_harness(args,root,receipt_file,locked=True)
        if result:return result
        # Keep the receipt when retained Mods still reference persistent sources.
        if component_file.exists() and not args.keep_mods:component_file.unlink()
        if not list((root/'receipts').glob('*.json')):
            user_path.remove_user_path(root)
    return 0
