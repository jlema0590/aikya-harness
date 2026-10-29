"""Correlate child CLI snapshots with one explicit native Flow invocation."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
from aikya.core import state


def _related(root, origin):
    if root == origin or origin in root.parents:
        return True
    # External worktrees share the same Git common directory. No checkout changes.
    def common(path):
        result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--git-common-dir'],
                                capture_output=True, text=True, timeout=2)
        if result.returncode:
            return None
        return (path / result.stdout.strip()).resolve()
    try:
        source = common(origin)
        return source is not None and source == common(root)
    except (OSError, subprocess.SubprocessError):
        return False


def context(root, session, command=None):
    result = {'root': str(Path(root).resolve()), 'session_id': session}
    try:
        raw = json.loads(os.environ.get('AIKYA_FLOW_CONTEXT', 'null'))
        if not isinstance(raw, dict) or raw.get('schema') != 1 or (command is not None and raw.get('command') != command):
            return result
        token, real_session = raw.get('invocation_id'), raw.get('session_id')
        if not isinstance(token, str) or not re.fullmatch(r'[a-f0-9]{32}', token):
            return result
        if (not isinstance(real_session, str) or not real_session or real_session == 'local'
                or len(real_session) > 180 or any(not c.isprintable() for c in real_session)
                or session not in (None, 'local', real_session)):
            return result
        origin, cache = Path(raw['origin_root']), Path(raw['cache_root'])
        if not origin.is_absolute() or not cache.is_absolute() or not _related(Path(result['root']), origin.resolve()):
            return result
        configured = os.environ.get('AIKYA_EXECUTION_CACHE')
        if configured and Path(configured).resolve() != cache.resolve():
            return result
        result.update(session_id=real_session, cache_root=str(cache), flow_origin=str(origin.resolve()), flow_invocation=token)
    except (ValueError, OSError, TypeError, KeyError):
        pass
    return result


def publish(context, snapshot, *, preview=None, focus='general'):
    token = context.get('flow_invocation')
    if not token:
        return
    origin = {**context, 'root': context['flow_origin']}
    folder = state.directory(origin, True)
    path = folder / ('flow-' + token + '.json')
    identity = state.identity(origin)
    header = {'schema': 1, 'identity': identity, 'session_id': context['session_id'],
              'invocation_id': token, 'command': snapshot['command']}
    entry = {'identity': snapshot['identity'], 'run_id': snapshot['run_id'],
             'mode': 'observed' if preview is None else 'preview' if preview else 'approved', 'focus': focus}
    with state.locked(folder):
        index = state.read(path) or {**header, 'runs': []}
        if any(index.get(key) != value for key, value in header.items()) or not isinstance(index.get('runs'), list):
            raise ValueError('Flow invocation index mismatch')
        rows = index['runs']
        if len(rows)>64 or any(not isinstance(row,dict) or not re.fullmatch(r'[a-f0-9]{64}',str(row.get('identity',''))) or not re.fullmatch(r'[a-zA-Z0-9-]{1,80}',str(row.get('run_id',''))) for row in rows):
            raise ValueError('Invalid Flow execution references')
        previous = next((i for i, row in enumerate(rows) if row.get('identity') == entry['identity'] and row.get('run_id') == entry['run_id']), None)
        if previous is not None:
            rows[previous] = entry
        elif len(rows) < 64:
            rows.append(entry)
        else:
            raise ValueError('Flow invocation has more than 64 executions')
        state.atomic(path, index)
