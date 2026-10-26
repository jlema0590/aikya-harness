"""Persist generated settings changes without copying unrelated user secrets."""
import base64
import copy
import json
from pathlib import Path
from . import state


def is_settings(name):
    return Path(name).name == 'settings.json'


def changes(before, after):
    result = []
    for name, raw in after.items():
        if not is_settings(name):
            continue
        previous = json.loads(base64.b64decode(before[name])) if name in before else {}
        current = json.loads(base64.b64decode(raw))
        record = {'path': name, 'created': name not in before, 'hooks_existed': 'hooks' in previous, 'groups': [], 'status': {}}
        for event, groups in current.get('hooks', {}).items():
            for group in groups:
                if group not in previous.get('hooks', {}).get(event, []):
                    record['groups'].append({'event': event, 'group': group, 'event_existed': event in previous.get('hooks', {})})
        for key in ('statusLine', 'subagentStatusLine'):
            if key in current and key not in previous:
                record['status'][key] = current[key]
        result.append(record)
    return result


def remove(records, runtime):
    prepared = []
    for record in records:
        path = state.safe(Path(record['path']))
        if not path.exists():
            continue
        current = json.loads(path.read_text(encoding='utf8')); updated = copy.deepcopy(current)
        hooks = updated.get('hooks', {})
        for item in record['groups']:
            groups = hooks.get(item['event'], [])
            if item['group'] in groups:
                groups.remove(item['group'])
            if not groups and not item['event_existed']:
                hooks.pop(item['event'], None)
        if not hooks and not record['hooks_existed']:
            updated.pop('hooks', None)
        for key, value in record['status'].items():
            if updated.get(key) == value:
                updated.pop(key)
        # A modified Aikya hook is not an owned unchanged hook. Retain its runtime.
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from strings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from strings(child)
        needle = str(runtime).replace('\\', '/')
        if any(needle in value.replace('\\', '/') for value in strings(updated)):
            raise ValueError('Edited owned hook retained; review before removing its runtime')
        prepared.append((path, updated, record['created']))
    for path, updated, created in prepared:
        if created and not updated:
            path.unlink()
        else:
            state.write_json(path, updated)
