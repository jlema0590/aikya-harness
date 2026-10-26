"""Owned installer state, serialized mutations and conservative file recovery."""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile

OWNER = {'schema': 1, 'generated_by': 'aikya-clean-installer'}


def safe(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlinked installer path: ' + str(path))
    return path


def write_json(path, data):
    safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='.aikya-', dir=path.parent)
    try:
        with os.fdopen(handle, 'w', encoding='utf8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextmanager
def installation_lock(root):
    safe(root)
    marker = safe(root / 'owner.json')
    if root.exists() and any(root.iterdir()) and (not marker.is_file() or json.loads(marker.read_text()) != OWNER):
        raise ValueError('Unowned application directory requires explicit review')
    root.mkdir(parents=True, exist_ok=True)
    lock = root / '.install.lock'
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError('Installation lock exists; another operation is in progress or needs recovery') from exc
    try:
        os.close(handle)
        if not marker.exists():
            write_json(marker, OWNER)
        yield
    finally:
        lock.unlink(missing_ok=True)


def snapshot(paths):
    result = {}
    for base in paths:
        safe(base)
        candidates = sorted(base.rglob('*')) if base.is_dir() else [base]
        for path in candidates:
            safe(path)
            if path.is_file():
                result[str(path)] = base64.b64encode(path.read_bytes()).decode('ascii')
    return result


def restore(before, after):
    preserved = []
    for name in sorted(set(before) | set(after), reverse=True):
        path = Path(name)
        try:
            safe(path)
            actual = base64.b64encode(path.read_bytes()).decode('ascii') if path.is_file() else None
            if actual != after.get(name):
                preserved.append(name); continue
            original = before.get(name)
            if original == actual:
                continue
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(base64.b64decode(original, validate=True))
        except (ValueError, OSError):
            preserved.append(name)
    return preserved


def activate(root: Path, receipt: dict) -> None:
    environment = Path(receipt['environment'])
    safe(environment)
    if not environment.is_relative_to(root / 'versions') or not environment.is_dir():
        raise ValueError('Activation requires an owned final-path environment')
    write_json(root / 'current.json', receipt)


from .options import receipt_path

def record_project_reference(target, prefix=None):
    """Track only projects initialized by an owned managed interpreter; never scan."""
    import sys
    prefix = Path(prefix or sys.prefix).resolve()
    if prefix.parent.parent.name != 'versions':
        return
    root = prefix.parents[2]
    marker = safe(root / 'owner.json')
    if not marker.is_file() or json.loads(marker.read_text()) != OWNER:
        return
    target = Path(target).resolve()
    record = {'schema': 1, 'target': str(target), 'environment': str(prefix)}
    name = hashlib.sha256(str(target).encode('utf8')).hexdigest() + '.json'
    with installation_lock(root):
        write_json(root / 'references' / name, record)


def active_references(root):
    result = []
    for path in sorted((root / 'references').glob('*.json')):
        safe(path)
        record = json.loads(path.read_text())
        target = Path(record['target']); environment = Path(record['environment'])
        if not target.is_absolute() or not environment.is_relative_to(root / 'versions'):
            raise ValueError('Unsafe initialized project reference')
        if (target / '.harness/project-profile.json').is_file():
            result.append(record)
    return result
