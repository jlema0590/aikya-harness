"""Compatibility-only bootstrap for source and bundled runtimes."""
from importlib import import_module
from pathlib import Path
import runpy
import sys
import importlib.util
import uuid
sys.dont_write_bytecode=True


def activate():
    base=Path(__file__).resolve().parent/'src'
    if (base/'aikya/__init__.py').is_file() and str(base) not in sys.path:
        sys.path.insert(0,str(base))


def load(name,entry_file=None,fresh=False):
    activate()
    from aikya.resource_paths import entry_context
    token=entry_context.set(entry_file)
    try:
        module=import_module(name)
        if not fresh:return module
        qualified=name+'__compat_'+uuid.uuid4().hex
        spec=importlib.util.spec_from_file_location(qualified,module.__file__)
        copied=importlib.util.module_from_spec(spec)
        sys.modules[qualified]=copied
        spec.loader.exec_module(copied)
        return copied
    finally:
        entry_context.reset(token)


def run(name,entry_file=None):
    activate()
    from aikya.resource_paths import entry_context
    token=entry_context.set(entry_file)
    try:runpy.run_module(name,run_name='__main__')
    finally:entry_context.reset(token)
