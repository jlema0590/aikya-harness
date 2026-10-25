"""Single destination inventory for source, registered and initialized runtimes."""
from dataclasses import dataclass
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from aikya.resource_paths import package_root,source_path,source_root
from aikya.documentation.layout import asset_bytes
from aikya.installation.compatibility import load_module_map, render_adapter

MODULES = json.loads((package_root() / 'module_map.json').read_text(encoding='utf8'))
HELPERS = {'scaffold', 'infrastructure', 'run_checks', 'skills_lint', 'docs_guard'}
EXECUTION_FILES = tuple(name + '.py' for name in MODULES if name in {
    'check_events', 'command_workflows', 'execution_state', 'execution_observer',
    'execution_config', 'execution_lifecycle', 'runtime_metrics', 'aikya_statusline',
    'aikya_subagent_statusline', 'odd_engine', 'agent_runtime', 'agent_loop',
    'agent_loop_state', 'agent_memory', 'memory_store', 'agent_memory_extract',
    'durable_io', 'code_quality', 'external_skills', 'skills_registry',
}) + ('requirements-agent-loop.txt', 'docs/AGENT_LOOP.md', 'docs/SECURITY_CONTROLS.md')
CORE_FILES = tuple(name + '.py' for name in MODULES if name not in HELPERS | {'context_budget'}) + (
    '_aikya_bootstrap.py', 'requirements-agent-loop.txt', 'docs/AGENT_LOOP.md', 'docs/SECURITY_CONTROLS.md',
)


@dataclass(frozen=True)
class AssetRecord:
    source: Path | None
    destination: Path
    kind: str
    producer: Callable[[], bytes] | None = None
    inputs: tuple[Path, ...] = ()
    root: Path | None = None

    def __post_init__(self):
        if (self.source is None) == (self.producer is None):
            raise ValueError('Asset requires exactly one file or generated producer')
        if self.source is None and not self.inputs:
            raise ValueError('Generated assets require provenance inputs')

    def checked_bytes(self, path: Path) -> bytes:
        boundary = self.root or path.parent
        if not path.absolute().is_relative_to(boundary.absolute()):
            raise ValueError('Runtime source escapes its selected root')
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)
                                    if p == boundary or boundary in p.parents):
            raise ValueError('Missing or unsafe runtime source: ' + str(path))
        return path.read_bytes()

    def read_bytes(self) -> bytes:
        if self.source is not None:
            return self.checked_bytes(self.source)
        for path in self.inputs:
            self.checked_bytes(path)
        raw = self.producer()
        if not isinstance(raw, bytes):
            raise ValueError('Generated runtime producer must return bytes')
        return raw

    def source_digest(self) -> str:
        digest = hashlib.sha256(self.read_bytes())
        for path in self.inputs:
            digest.update(str(path).encode('utf8'))
            digest.update(hashlib.sha256(self.checked_bytes(path)).digest())
        return digest.hexdigest()


def selected_package(source: Path) -> Path:
    package = source / 'src/aikya'
    if not package.is_dir() and source == package_root() / 'resources/distribution':
        package = package_root()
    if not (package / 'module_map.json').is_file() or any(p.is_symlink() for p in (package, *package.parents) if p == package or p == source or source in p.parents):
        raise ValueError('Incomplete packaged Aikya source')
    return package


def resolve_runtime_asset(source: Path, relative: str, *, _modules=None) -> AssetRecord:
    source, relative = Path(source), Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe runtime asset path')
    package = selected_package(source)
    boundary = package if source == package / 'resources/distribution' else source
    mapping = package / 'module_map.json'
    modules = load_module_map(mapping) if _modules is None else _modules
    helper = relative.as_posix().startswith('template/scripts/harness/') and relative.stem in HELPERS
    if relative.suffix == '.py' and relative.stem in modules and (len(relative.parts) == 1 or helper):
        template = source_path(source, 'compatibility/adapter.py.tmpl')
        renderer = package / 'installation/compatibility.py'
        raw = render_adapter(relative.stem, modules, AssetRecord(template, relative, 'resource', root=boundary).read_bytes())
        return AssetRecord(None, relative, 'adapter', lambda: raw, (mapping, renderer, template), boundary)
    path = source_path(source, 'compatibility/_aikya_bootstrap.py') if relative == Path('_aikya_bootstrap.py') else source_path(source, relative)
    return AssetRecord(path, relative, 'adapter', root=boundary)


def runtime_assets(source: Path, target_kind: str, *, methodology=None) -> tuple[AssetRecord, ...]:
    if target_kind not in ('registration', 'initialized'):
        raise ValueError('Unsupported runtime target kind')
    source = Path(source)
    package = selected_package(source)
    boundary = package if source == package / 'resources/distribution' else source
    modules = load_module_map(package / 'module_map.json')
    result = [resolve_runtime_asset(source, name, _modules=modules) for name in CORE_FILES]
    if target_kind == 'initialized' and methodology == 'odd':
        result = [asset for asset in result if asset.destination != Path('sdd_engine.py')]
    for name in sorted(HELPERS):
        result.append(resolve_runtime_asset(source, 'template/scripts/harness/' + name + '.py', _modules=modules))
        if target_kind == 'initialized':
            result.append(resolve_runtime_asset(source, name + '.py', _modules=modules))
    for path in sorted(package.rglob('*')):
        rel = path.relative_to(package)
        if 'resources' not in rel.parts and '__pycache__' not in rel.parts and (path.suffix == '.py' or rel == Path('module_map.json')):
            if path.is_symlink():
                raise ValueError('Symlinked package input: ' + str(path))
            if path.is_file():
                result.append(AssetRecord(path, Path('src/aikya') / rel, 'package', root=package))
    for folder in ('template', 'examples', 'aikya-skills', 'engineering', 'sdd-templates', 'claude-templates', 'aikya-template', 'migrations', 'compatibility'):
        if folder == 'examples' and target_kind == 'initialized':
            continue
        origin = source_path(source, folder)
        if folder == 'examples' and not origin.exists():
            continue
        if not origin.is_dir() or origin.is_symlink():
            raise ValueError('Missing or unsafe runtime resource: ' + folder)
        for path in sorted(origin.rglob('*')):
            rel = Path(folder) / path.relative_to(origin)
            if rel.as_posix().startswith('template/scripts/harness/') and path.stem in HELPERS:
                continue
            if path.is_symlink():
                raise ValueError('Symlinked resource input: ' + str(path))
            if path.is_file() and '__pycache__' not in rel.parts and path.suffix != '.pyc' and not rel.is_relative_to('examples/documentation/generated') and not (path.name.startswith('.env') and path.name != '.env.example'):
                result.append(AssetRecord(path, rel, 'resource', root=boundary))
    viewer = package / 'resources/memory-viewer'
    if viewer.is_dir():
        for path in sorted(viewer.iterdir()):
            if path.is_file():
                result.append(AssetRecord(path, Path('src/aikya/resources/memory-viewer') / path.name, 'resource', root=package))
    destinations = [r.destination for r in result]
    if len(destinations) != len(set(destinations)):
        raise ValueError('Runtime asset destination collision')
    for record in result:
        record.read_bytes()
    return tuple(result)


SOURCE_GALLERY='https://github.com/jlema0590/aikya-harness/blob/08db4879ae3a8697c91adb0cc46bd76e333c693b/examples/documentation/generated/README.es.md'

def runtime_asset_bytes(relative:Path,raw:bytes)->bytes:
    """Keep source navigation local and registered-runtime navigation resolvable."""
    if relative==Path('examples/documentation/README.md'):
        raw=raw.replace(b'](generated/README.es.md)',(']('+SOURCE_GALLERY+')').encode('utf8'))
    return asset_bytes(relative,raw)
