"""Resolve source assets independently from registered and initialized destinations."""
from importlib.resources import files
import os
from pathlib import Path
from contextvars import ContextVar

entry_context = ContextVar('aikya_entry_file', default=None)

PREFIXES = {
    'template': 'project_template', 'aikya-skills': 'commands',
    'engineering': 'engineering', 'sdd-templates': 'sdd_templates',
    'claude-templates': 'claude_templates',
    'aikya-template': 'aikya-template', 'migrations': 'migrations',
    'compatibility': 'compatibility',
}


def package_root() -> Path:
    return Path(str(files('aikya'))).resolve()


def source_root() -> Path:
    package = package_root()
    candidate = package.parent.parent
    if package.parent.name == 'src' and (package / 'module_map.json').is_file():
        return candidate
    return package / 'resources/distribution'


def source_path(root: Path, relative: str | Path) -> Path:
    root = Path(root)
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Asset source must be relative and contained')
    legacy = root / relative
    if legacy.exists():
        return legacy
    resources = root / 'src/aikya/resources'
    if root == package_root() / 'resources/distribution':
        resources = root.parent
    if relative.parts and relative.parts[0] in PREFIXES:
        return resources / PREFIXES[relative.parts[0]] / Path(*relative.parts[1:])
    return legacy


def project_root() -> Path:
    override = os.environ.get('CLAUDE_PROJECT_DIR')
    if override:
        return Path(override).resolve()
    entry = entry_context.get()
    if entry:
        entry = Path(entry).resolve()
        if entry.parent.name == 'harness' and entry.parent.parent.name == 'scripts':
            return entry.parents[3] if entry.parents[2].name == 'aikya' else entry.parents[2]
    root = source_root()
    if root.name == 'harness' and root.parent.name == 'scripts' and root.parent.parent.name == 'aikya':
        return root.parents[2]
    return root if root.name != 'distribution' else Path.cwd()
