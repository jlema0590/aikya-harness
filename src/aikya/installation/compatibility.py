"""Deterministic compatibility launchers; mapping entries are data, never code."""
import json
import keyword
from pathlib import Path

HELPERS = frozenset({'scaffold', 'infrastructure', 'run_checks', 'skills_lint', 'docs_guard'})


def identifier(value):
    return isinstance(value, str) and value.isidentifier() and not keyword.iskeyword(value)


def load_module_map(path: Path) -> dict[str, str]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate runtime module name: ' + key)
            result[key] = value
        return result

    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing or unsafe runtime module mapping')
    modules = json.loads(path.read_text(encoding='utf8'), object_pairs_hook=unique)
    if not isinstance(modules, dict) or not modules:
        raise ValueError('Runtime mapping must be a nonempty object')
    for name, target in modules.items():
        if not identifier(name) or not isinstance(target, str) or not all(identifier(p) for p in target.split('.')):
            raise ValueError('Unsafe runtime module mapping')
        implementation = path.parent / (target.replace('.', '/') + '.py')
        if not implementation.is_file() or any(p.is_symlink() for p in (implementation, *implementation.parents)):
            # macOS /tmp itself may be a system symlink; only inspect the selected package.
            if not implementation.is_file() or any(p.is_symlink() for p in (implementation, *implementation.parents) if p == path.parent or path.parent in p.parents):
                raise ValueError('Missing or unsafe Aikya implementation: ' + target)
    return modules


def render_adapter(name: str, modules: dict[str, str], template: bytes) -> bytes:
    if name not in modules or not identifier(name):
        raise ValueError('Unknown runtime adapter: ' + str(name))
    target = modules[name]
    if not isinstance(target, str) or not all(identifier(p) for p in target.split('.')):
        raise ValueError('Unsafe runtime module target')
    if template.count(b'@@MODULE@@') != 2 or template.count(b'@@FRESH@@') != 1:
        raise ValueError('Malformed runtime adapter template')
    fresh = b'True' if name in HELPERS else b'__name__ != Path(__file__).stem'
    result = template.replace(b'@@MODULE@@', ('aikya.' + target).encode('ascii')).replace(b'@@FRESH@@', fresh)
    if b'@@' in result:
        raise ValueError('Unresolved runtime adapter placeholder')
    compile(result, name + '.py', 'exec')
    return result
