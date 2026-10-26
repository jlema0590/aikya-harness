"""Project/private memory locations and identity, never a second retrieval engine."""
from __future__ import annotations
import os,re
from pathlib import Path
from aikya.core.checkpoints import identity,safe_file
from aikya.documentation.layout import index_paths,stamp,write_document
from aikya.storage import atomic_write

SCOPES=('project','private')


def store_root(root,scope='project',private_root=None,*,identity_key=None,create=False):
    root=Path(root).absolute()
    if scope not in SCOPES:raise ValueError('Memory scope must be project or private')
    if scope=='project':
        base=safe_file(root,'aikya/docs/memory/MEMORY.md').parent
        if create:index_paths(root);base.mkdir(parents=True,exist_ok=True)
        return base
    key=identity_key or identity(root)
    if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('Invalid prior project identity')
    base=Path(private_root).expanduser().absolute() if private_root is not None else Path.home()/'.aikya/memory'
    if any(p.is_symlink() for p in (base,*base.parents) if p not in (Path('/tmp'),Path('/var'))):raise ValueError('Symlinked private memory root')
    base=base.resolve()
    if base.is_relative_to(root.resolve()):raise ValueError('Private memories must live outside the project')
    target=base/key
    if target.is_symlink() or (target.exists() and not target.is_dir()):raise ValueError('Invalid private memory store')
    if create:
        base.mkdir(parents=True,exist_ok=True,mode=0o700);target.mkdir(exist_ok=True,mode=0o700)
        if os.name!='nt':os.chmod(base,0o700);os.chmod(target,0o700)
    return target


def note_path(root,ident,scope='project',private_root=None,*,identity_key=None):
    if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{24}',ident):raise ValueError('Invalid memory ID')
    path=store_root(root,scope,private_root,identity_key=identity_key)/(ident+'.md')
    if path.is_symlink():raise ValueError('Symlinked memory note')
    return path


def private_subdir(root,section,private_root=None):
    if section not in ('extractions','migrations'):raise ValueError('Invalid private memory section')
    path=store_root(root,'private',private_root,create=True)/section
    if path.is_symlink() or (path.exists() and not path.is_dir()):raise ValueError('Unsafe private memory section')
    path.mkdir(exist_ok=True,mode=0o700)
    if os.name!='nt':os.chmod(path,0o700)
    return path


def write(root,path,body,scope):
    if path.is_symlink():raise ValueError('Symlinked memory note')
    if scope=='project':return write_document(root,'memory/'+path.name,body,replace_generated=True)
    atomic_write(path,stamp(body),mode=0o600)
    return str(path)


def reference(root,path,scope):
    return path.relative_to(root).as_posix() if scope=='project' else str(path)
