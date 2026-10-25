"""Explicit viewers share the project's observer through independently owned leases."""
from contextlib import contextmanager
import time
import uuid
from aikya.code_index.hooks import process_event


@contextmanager
def observer_client(root):
    session = 'memory-client-' + uuid.uuid4().hex
    process_event(root, {'hook_event_name': 'SessionStart', 'session_id': session})
    try:
        yield lambda: process_event(root, {'hook_event_name': 'UserPromptSubmit', 'session_id': session})
    finally:
        try:
            process_event(root, {'hook_event_name': 'SessionEnd', 'session_id': session})
        except (OSError, ValueError):
            pass  # A deleted/disabled project cannot acquire new observation permissions.


def wait_for_observer(stop_event, heartbeat):
    next_heartbeat = time.monotonic() + 30
    while not stop_event.wait(1):
        if time.monotonic() >= next_heartbeat:
            heartbeat()
            next_heartbeat = time.monotonic() + 30
