"""Generate real installed aliases for tests that exercise legacy entry context."""
import atexit
import importlib.util
from pathlib import Path
import tempfile
from aikya.installation.assets import resolve_runtime_asset
from aikya.resource_paths import source_root

_TEMPORARIES = []


def generated_bytes(name):
    return resolve_runtime_asset(source_root(), name).read_bytes()


def module_spec(name, path):
    path = Path(path)
    if path.name.endswith('.py') and (path.parent == source_root() or path.is_relative_to(source_root() / 'src/aikya/resources/project_template/scripts/harness')):
        try:
            asset = resolve_runtime_asset(source_root(), path.name)
        except ValueError:
            return importlib.util.spec_from_file_location(name, path)
        temporary = tempfile.TemporaryDirectory(prefix='aikya-installed-helper-')
        _TEMPORARIES.append(temporary)
        root = Path(temporary.name) / 'project/aikya/scripts/harness'
        root.mkdir(parents=True)
        (root / path.name).write_bytes(asset.read_bytes())
        (root / '_aikya_bootstrap.py').write_bytes(generated_bytes('_aikya_bootstrap.py'))
        return importlib.util.spec_from_file_location(name, root / path.name)
    return importlib.util.spec_from_file_location(name, path)


atexit.register(lambda: [temporary.cleanup() for temporary in _TEMPORARIES])
