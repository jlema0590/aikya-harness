"""Explicit component selection and resumable native plugin ownership."""
from pathlib import Path
import re

from .options import ComponentPlan, plan_components

def validate_receipt(record, scope, target):
    expected = 'user' if scope == 'global' else 'project'
    if (not isinstance(record, dict) or record.get('schema') != 1
            or record.get('scope') != expected or record.get('target') != (str(target) if target else None)):
        raise ValueError('Component receipt scope/target does not match this operation')
    selected = record.get('selected', [])
    plugins = record.get('plugins', {})
    if (not isinstance(selected, list) or not isinstance(plugins, dict)
            or any(not isinstance(n,str) or not re.fullmatch(r'aikya-[a-z0-9-]+',n) for n in [*selected,*plugins])):
        raise ValueError('Invalid component receipt selection')
    for value in plugins.values():
        if not isinstance(value,dict) or not isinstance(value.get('remove_on_uninstall'),bool):
            raise ValueError('Invalid component ownership receipt')


def scoped(record, plan):
    if record.get('scope') != plan.scope:
        return False
    if plan.scope == 'project':
        target = record.get('projectPath')
        if not target or Path(target).resolve() != Path(plan.target).resolve():
            return False
    return True


def same_path(left, right):
    return bool(left and right) and Path(left) == Path(right)


def check_source(bundle, receipt, adapter, managed_sources=()):
    markets = [p for p in adapter.marketplaces() if p.get('name') == 'aikya-mods']
    if not markets:
        return False
    source = markets[0].get('path')
    shared = same_path(source,bundle.path) and any(same_path(source,p) for p in managed_sources)
    if not shared and (not receipt.get('marketplace_owned') or not any(same_path(source,p) for p in (receipt.get('source'),receipt.get('pending_source')))):
        raise ValueError('Existing aikya-mods marketplace is not owned or its source changed; use --mods none or review adoption')
    if Path(source) != bundle.path:
        managed = {name + '@aikya-mods' for name in receipt.get('plugins', {})}
        owner=ComponentPlan((),receipt.get('scope'),receipt.get('target'),False)
        if any(p.get('id','').endswith('@aikya-mods') and
               (p['id'] not in managed or not scoped(p,owner)) for p in adapter.inventory()):
            raise ValueError('Marketplace source is shared with unmanaged plugins or another scope; preserve it and review update')
    return True


def install_plugins(bundle, plan, receipt, adapter, save, managed_sources=()):
    selected = tuple(sorted(bundle.plugins)) if plan.selected == ('*',) else plan.selected
    if any(name not in bundle.plugins for name in selected):
        raise ValueError('Selected mod is missing from the verified catalog')
    check_source(bundle, receipt, adapter, managed_sources)
    inventory = {p['id']: p for p in adapter.inventory() if scoped(p, plan)}
    receipt.setdefault('plugins', {})
    receipt.update(schema=1, scope=plan.scope, target=plan.target, status='partial',
                   selected=sorted(set(receipt.get('selected', [])) | set(selected)))
    save()
    # Record intent before external mutations so a crash remains recoverable.
    receipt.update(marketplace_owned=True, pending_source=str(bundle.path))
    save()
    try:
        adapter.command('plugin','marketplace','add',str(bundle.path),'--scope',plan.scope,'--json')
        receipt.update(source=str(bundle.path), version=bundle.version)
        receipt.pop('pending_source', None); save()
        for name in selected:
            current = inventory.get(name + '@aikya-mods')
            owned = receipt['plugins'].get(name)
            if current and not owned and not plan.explicit:
                continue  # Never adopt a pre-existing plugin through defaults.
            if current and not owned and not same_path(current.get('readFromFolder'),bundle.path/'mods'/name):
                raise ValueError('Existing plugin source requires explicit review: ' + name)
            if current and owned and current.get('readFromFolder') and not any(same_path(current['readFromFolder'],p) for p in (owned.get('source'),owned.get('pending_source'))):
                raise ValueError('Managed plugin source was modified: ' + name)
            record = owned or {'remove_on_uninstall': current is None}
            if current and owned and current.get('version') == bundle.plugins[name] and owned.get('version') == bundle.plugins[name]:
                continue
            record.update(pending_version=bundle.plugins[name], pending_source=str(bundle.path / 'mods' / name))
            receipt['plugins'][name] = record; save()
            action = 'update' if current else 'install'
            adapter.command('plugin',action,name+'@aikya-mods','--scope',plan.scope,'--json')
            record.update(version=record.pop('pending_version'), source=record.pop('pending_source'))
            save()
        receipt['selected'] = sorted(receipt['plugins'])
        receipt['status'] = 'complete'; save()
    except BaseException:
        receipt['status'] = 'partial'; save(); raise
    return receipt


def uninstall_plugins(receipt, adapter, save):
    receipt['status'] = 'partial'; save()
    plan = ComponentPlan((),receipt['scope'],receipt.get('target'),False)
    inventory = {p['id']:p for p in adapter.inventory() if scoped(p,plan)}
    for name, record in list(receipt.get('plugins',{}).items()):
        current = inventory.get(name+'@aikya-mods')
        if current and record.get('remove_on_uninstall'):
            if current.get('version') not in (record.get('version'), record.get('pending_version')) or (current.get('readFromFolder') and not any(same_path(current['readFromFolder'],p) for p in (record.get('source'),record.get('pending_source')))):
                raise ValueError('Modified plugin preserved: '+name)
            adapter.command('plugin','uninstall',name+'@aikya-mods','--scope',plan.scope,'--json','--keep-data')
        del receipt['plugins'][name]; save()
    remaining = [p for p in adapter.inventory() if p.get('id','').endswith('@aikya-mods')]
    markets = [p for p in adapter.marketplaces() if p.get('name') == 'aikya-mods']
    if not remaining and receipt.get('marketplace_owned') and markets:
        if not any(same_path(markets[0].get('path'),p) for p in (receipt.get('source'),receipt.get('pending_source'))):
            raise ValueError('Modified marketplace preserved')
        adapter.command('plugin','marketplace','remove','aikya-mods','--scope',plan.scope,'--json')
    receipt.update(status='removed',selected=[]); save()
