"""Session-owned observation and bounded dirty hints; never invokes an assistant."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from aikya.core.checkpoints import identity, safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from .policy import excluded, load_policy, project_root, read_source

LEASES = '.harness/state/memory-view/sessions.json'


def _leases(root):
    try:
        data = json.loads(read_source(root, LEASES, 16000))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or len(data) > 100:
        raise ValueError('Invalid memory observer sessions')
    return {key: value for key, value in data.items() if isinstance(key, str) and len(key) == 64
            and type(value) in (int, float) and 0 <= time.time() - value < 21600}


def active_sessions(root):
    return bool(_leases(root))


def mark_dirty(root, paths):
    root = project_root(root)
    if not load_policy(root).enabled:
        return
    if not isinstance(paths, list) or len(paths) > 100:
        raise ValueError('Dirty hint exceeds the scoped path limit')
    clean = []
    for path in paths:
        safe_file(root, path)
        if not excluded(path):
            clean.append(path)
    if not clean:
        return
    path = safe_file(root, '.harness/state/code-index/dirty.json')
    atomic_write(path, json.dumps({'identity': identity(root), 'paths': clean,
                                  'at': time.time()}, sort_keys=True) + '\n')


def process_event(root, event):
    root = project_root(root)
    policy = load_policy(root)
    hook = event.get('hook_event_name')
    if hook not in ('SessionStart', 'SessionEnd', 'UserPromptSubmit', 'PostToolUse'):
        return
    session = event.get('session_id')
    if not isinstance(session, str) or not session or len(session) > 200:
        return
    path = safe_file(root, LEASES)
    if not policy.watch and hook != 'SessionEnd':
        return
    if hook == 'SessionEnd' and not path.exists():
        return
    guard = safe_file(root, '.harness/state/memory-view/launcher/.lock').parent
    guard.mkdir(parents=True, exist_ok=True)
    with locked(guard):
        leases = _leases(root)
        key = hashlib.sha256(session.encode()).hexdigest()
        if hook == 'SessionEnd':
            leases.pop(key, None)
        else:
            if key not in leases and len(leases) >= 100:
                raise ValueError('Project observer session limit reached')
            leases[key] = time.time()
        atomic_write(path, json.dumps(leases, sort_keys=True) + '\n')
        if hook == 'SessionEnd':
            return
        if hook == 'PostToolUse':
            raw = event.get('tool_input', {}).get('file_path')
            if isinstance(raw, str):
                candidate = Path(raw)
                try:
                    relative = candidate.relative_to(root).as_posix() if candidate.is_absolute() else raw
                    mark_dirty(root, [relative])
                except ValueError:
                    pass
        try:
            status = json.loads(read_source(root, '.harness/state/memory-view/status.json', 16000))
            if status.get('state') != 'Stopped' and time.time() - status.get('heartbeat', 0) < 10:
                return
        except (FileNotFoundError, ValueError):
            pass
        package_parent = Path(__file__).resolve().parents[2]
        bootstrap = 'import sys;sys.path.insert(0,sys.argv.pop(1));from aikya.cli.main import main;raise SystemExit(main())'
        command = [sys.executable, '-I', '-B', '-c', bootstrap, str(package_parent),
                   'memory', '--target', str(root), '--watch', '--session-managed']
        with open(os.devnull, 'wb') as sink:
            process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=sink, stderr=sink,
                                       start_new_session=os.name != 'nt', close_fds=True)
        threading.Thread(target=process.wait, daemon=True).start()
        # Avoid launching duplicates during the initial scan. The child publishes the real status.
        atomic_write(safe_file(root, '.harness/state/memory-view/status.json'),
                     json.dumps({'state': 'Starting', 'heartbeat': time.time(), 'pid': process.pid, 'session_managed': True}) + '\n')
