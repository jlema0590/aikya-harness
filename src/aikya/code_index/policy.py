"""Explicit per-checkout index policy and conservative filesystem boundaries."""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import stat
from aikya.core.checkpoints import safe_file
from aikya.storage import atomic_write
from aikya.discovery.scanner import safe_scope
from .contracts import IndexOptions

POLICY = '.aikya/code-index.json'
EXCLUDED = frozenset(('.git', '.harness', '.aikya', '.claude', '.ssh', '.aws',
    'secrets', 'credentials', 'node_modules', '.venv', 'venv', '__pycache__',
    'dist', 'build', 'target', 'vendor', 'coverage', '.terraform', '.gradle',
    '.next', '.nuxt', '.idea', '.pytest_cache', '.mypy_cache', '.ruff_cache'))
CODE_SUFFIXES = frozenset(('.py', '.pyi', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx',
    '.java', '.cs', '.go', '.kt', '.kts', '.swift', '.dart', '.rs', '.php', '.rb',
    '.c', '.h', '.cpp', '.hpp', '.cc', '.sh', '.ps1', '.sql', '.tf', '.vue', '.svelte'))


def project_root(root):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Existing regular project directory required')
    return root.resolve()


def excluded(relative):
    parts = relative.lower().split('/')
    return (any(p in EXCLUDED or p.startswith(('.env', 'credentials.', '.aikya-durable-'))
                or p.endswith(('.pem', '.key', '.p12', '.pfx', '.keystore')) for p in parts)
            or relative.startswith(('aikya/scripts/', 'aikya/docs/memory/view/')))


def read_source(root, relative, limit):
    path = safe_file(root, relative)
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('Input exceeds the configured read limit')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(fd)
        current = safe_file(root, relative).stat()
        if (len(raw) > limit or (before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_ino, after.st_size, after.st_mtime_ns)
                or (current.st_ino, current.st_dev) != (after.st_ino, after.st_dev)):
            raise ValueError('Input changed during bounded inspection')
        return raw
    finally:
        os.close(fd)


def load_policy(root):
    root = project_root(root)
    path = safe_file(root, POLICY)
    if not path.exists():
        return IndexOptions()
    value = json.loads(read_source(root, POLICY, 16000))
    if (not isinstance(value, dict) or value.get('schema') != 1
            or value.get('generated_by') != 'aikya-code-index'):
        raise ValueError('Custom or incompatible code index policy; preserved')
    for key in ('enabled', 'watch', 'auto_export'):
        if type(value.get(key)) is not bool:
            raise ValueError('Invalid code index policy flag')
    defaults = asdict(IndexOptions())
    for key in ('max_files', 'max_file_bytes', 'max_sync_bytes'):
        if type(value.get(key)) is not int or not 1 <= value[key] <= defaults[key]:
            raise ValueError('Index limit exceeds the supported bounds')
    value.setdefault('scope', '.')
    safe_scope(root, value['scope'])
    return IndexOptions(**{key: value[key] for key in defaults})


def configure(root, *, approved=False, manage_ignore=True, scope='.'):
    if approved is not True:
        raise ValueError('Project memory configuration requires authorization')
    root = project_root(root)
    path = safe_file(root, POLICY)
    if path.exists():
        return load_policy(root)
    safe_scope(root, scope)
    options = IndexOptions(enabled=True, watch=True, auto_export=True, scope=scope)
    atomic_write(path, json.dumps({'schema': 1, 'generated_by': 'aikya-code-index',
                                  **asdict(options)}, indent=2) + '\n')
    ignore = safe_file(root, '.gitignore')
    if not manage_ignore:
        return options
    previous = read_source(root, '.gitignore', 1048576).decode('utf8') if ignore.exists() else ''
    patterns = ('.harness/state/', 'aikya/docs/memory/view/index.html')
    missing = [p for p in patterns if p not in previous.splitlines()]
    if missing:
        atomic_write(ignore, previous.rstrip() + '\n\n# Aikya regenerable local memory\n' + '\n'.join(missing) + '\n')
    return options


def content_hash(raw):
    return hashlib.sha256(raw).hexdigest()
