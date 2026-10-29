"""Explicit binary-only parser provisioning from the verified release manifest."""
import hashlib
from pathlib import Path
from . import download, environment

PINS = {'tree-sitter': '0.25.2', 'tree-sitter-java': '0.23.5',
        'tree-sitter-javascript': '0.25.0', 'tree-sitter-typescript': '0.23.2',
        'tree-sitter-c-sharp': '0.23.1', 'tree-sitter-go': '0.25.0', 'tree-sitter-dart': '0.1.0'}


def selection(value, previous, action):
    selected = value if value is not None else (previous or {}).get('code_index', 'none') if action == 'update' else value or 'none'
    requirements(selected)
    return selected


def requirements(selected):
    if selected not in ('none', 'dart', 'all'):
        raise ValueError('Select code-index none, dart or all')
    names = list(PINS) if selected == 'all' else ['tree-sitter', 'tree-sitter-dart'] if selected == 'dart' else []
    return [name+'=='+PINS[name] for name in names]


def prepare(selected, version, destination, offline_dir=None):
    wanted = requirements(selected)
    if not wanted:
        return []
    base = download.REPOSITORY+'/releases/download/v'+download.validate_version(version)+'/'
    def read(name, limit=download.LIMIT):
        if offline_dir is None:
            return download.https_bytes(base+name, limit)
        path = Path(offline_dir)/name
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Missing or unsafe offline parser asset: '+name)
        return path.read_bytes()
    hashes = download.parse_checksums(read('SHA256SUMS',128*1024))
    paths = []; total = 0
    for requirement in wanted:
        name, version_pin = requirement.split('==')
        prefix = name.replace('-', '_')+'-'+version_pin+'-'
        matches = [n for n in hashes if n.startswith(prefix) and n.endswith('.whl')]
        if not matches:
            raise ValueError('Verified release has no binary wheels for '+requirement)
        for filename in matches:
            raw = read(filename); total += len(raw)
            if total > download.LIMIT or hashlib.sha256(raw).hexdigest() != hashes[filename]:
                raise ValueError('Parser wheel integrity or total size limit failed')
            destination.mkdir(parents=True, exist_ok=True)
            path = destination/filename
            if path.exists() or path.is_symlink():
                raise ValueError('Parser staging destination exists')
            path.write_bytes(raw);paths.append(path)
    return paths


def provision(python, selected, wheels):
    wanted = requirements(selected)
    if not wanted:
        return
    if not wheels:
        raise ValueError('Selected parsers require verified binary artifacts')
    # pip chooses compatible ABI/platform tags; it cannot resolve from a network,
    # compile source, install dependencies or silently fall back to another version.
    directory = Path(wheels[0]).parent
    environment.run(python, '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps',
                    '--only-binary=:all:', '--find-links', directory, *wanted)
    names = [r.split('==')[0] for r in wanted]
    environment.run(python, '-c', 'import importlib.metadata as m;'+
                    ';'.join('assert m.version('+repr(n)+')=='+repr(PINS[n]) for n in names))
