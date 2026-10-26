"""One stoppable project observer coordinates incremental indexing and export."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import threading
import time
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from aikya.code_index.policy import load_policy, project_root
from aikya.code_index.sync import sync
from aikya.code_index.watch import observe_paths
from .contracts import WatchOptions, WatchStatus
from .export import export_view
from .publication import read_publication

STATE = '.harness/state/memory-view/status.json'


def publish_if_changed(root, *, now=None):
    before = None
    try:
        _, before = read_publication(root)
    except (OSError, ValueError):
        pass
    result = export_view(root)
    return result if result.published_generation != before else None


def _next_expiry(root, now):
    snapshot, _ = read_publication(root)
    times = []
    for node in snapshot.nodes:
        if node['type'] != 'memory':
            continue
        note = node['details']
        times.extend(t for t in (note['created_at'], note['created_at'] + note['ttl_days'] * 86400) if t > now)
    return min(times, default=float('inf'))


def watch_project(root, *, options=None, stop_event=None, session_managed=False):
    root = project_root(root)
    options = options or WatchOptions()
    stop_event = stop_event or threading.Event()
    if not load_policy(root).watch:
        raise ValueError('Project watch policy is disabled; no observer started')
    status_path = safe_file(root, STATE)
    guard = safe_file(root, '.harness/state/memory-view/observer/.lock').parent
    guard.mkdir(parents=True, exist_ok=True)
    status = WatchStatus()

    def save():
        if not root.is_dir():
            return
        safe_file(root,STATE)
        atomic_write(status_path, json.dumps({**asdict(status), 'pid': os.getpid(),
                                             'session_managed': session_managed,
                                             'heartbeat': time.time()}, sort_keys=True) + '\n')
    with locked(guard):
        previous = None
        first_change = last_change = None
        last_sync = float('-inf')
        next_expiry = float('inf')
        try:
            while not stop_event.is_set():
                policy = load_policy(root)
                if not policy.watch:
                    break
                if session_managed:
                    from aikya.code_index.hooks import active_sessions
                    if not active_sessions(root):
                        break
                signature, diagnostics = observe_paths(root, policy)
                monotonic = time.monotonic()
                if signature != previous:
                    first_change = monotonic if first_change is None else first_change
                    last_change, previous = monotonic, signature
                pending = first_change is not None
                settled = pending and (monotonic - last_change >= options.debounce_ms / 1000 or
                                       monotonic - first_change >= options.max_batch_wait_ms / 1000)
                due = last_sync == float('-inf') or monotonic - last_sync >= options.reconcile_interval_s or time.time() >= next_expiry
                if settled or due:
                    status.state, status.pending_count = 'Updating', int(pending)
                    save()
                    try:
                        result = sync(root, full=True)
                        status.index_generation = result.generation
                        status.diagnostics = result.diagnostics + diagnostics
                        if policy.auto_export:
                            publication = export_view(root)
                            status.published_generation = publication.published_generation
                            status.coverage = publication.coverage
                            status.diagnostics.extend(publication.diagnostics)
                            next_expiry = _next_expiry(root, time.time())
                        partial = result.status == 'partial' or status.diagnostics or any(v in ('partial', 'invalid', 'missing') for v in status.coverage.values())
                        status.state = 'Partial' if partial else 'Up to date'
                        if not policy.auto_export:
                            status.state = 'Watching'
                            status.coverage['viewer'] = 'disabled'
                        status.pending_count, status.last_verified_at = 0, time.time()
                    except (OSError, ValueError, UnicodeError, TypeError):
                        status.state = 'Partial'
                        status.diagnostics = ['local_update_failed; last publication retained']
                        status.pending_count = int(pending)
                    last_sync = time.monotonic()
                    first_change = last_change = None
                elif pending:
                    status.state, status.pending_count = 'Updating', 1
                save()
                stop_event.wait(options.poll_interval_ms / 1000)
        finally:
            status.state = 'Stopped'
            save()
