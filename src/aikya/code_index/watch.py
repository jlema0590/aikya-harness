"""Cheap metadata observations trigger hash reconciliation in the shared writer."""
from .policy import read_source, content_hash
from .scan import inventory


def observe_paths(root, policy):
    paths, diagnostics = inventory(root, policy, documents=True)
    signature = []
    for path in paths:
        try:
            info = (root / path).stat()
            signature.append((path, info.st_size, info.st_mtime_ns, info.st_ino))
        except OSError:
            signature.append((path, 'unavailable'))
    # Control changes matter even though they are never included in memory content.
    for name in ('.aikya/code-index.json', '.gitignore', '.harness/state/code-index/dirty.json'):
        try:
            signature.append((name, content_hash(read_source(root, name, 16000))))
        except (OSError, ValueError):
            signature.append((name, 'unavailable'))
    return tuple(signature), diagnostics
