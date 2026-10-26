"""Shared durable replacement for authoritative documents and checkpoints."""
from __future__ import annotations
import os
import tempfile
from pathlib import Path


def atomic_write(path, raw, *, mode=None):
    path=Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Symlinked durable destination')
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=raw.encode('utf8') if isinstance(raw,str) else raw
    fd,name=tempfile.mkstemp(prefix='.aikya-durable-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            if mode is not None and hasattr(os,'fchmod'):os.fchmod(stream.fileno(),mode)
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
        if hasattr(os,'O_DIRECTORY'):
            directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name)
