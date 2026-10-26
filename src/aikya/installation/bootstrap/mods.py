"""Verified official Mods bundles; sources persist while Claude references them."""
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile
from . import download, state

REPOSITORY = 'https://github.com/jlema0590/aikya-mods'
LATEST = 'https://api.github.com/repos/jlema0590/aikya-mods/releases/latest'


@dataclass(frozen=True)
class VerifiedModsBundle:
    version: str
    path: Path
    plugins: dict
    claude_version: str
    hashes: tuple


def resolve_version(version, offline_dir=None):
    if offline_dir and version in (None, 'latest'):
        raise ValueError('Offline Mods installation requires --mods-version X.Y.Z')
    return download.resolve_version(version, offline_dir, LATEST)


def storage_root():
    override = os.environ.get('AIKYA_MODS_HOME')
    if override:
        return Path(override).expanduser().absolute()
    home = Path.home().resolve()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA') or home / 'AppData/Local') / 'Aikya/Mods'
    if sys.platform == 'darwin':
        return home / 'Library/Application Support/Aikya/Mods'
    return Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share') / 'aikya-mods'


def asset(version, name, offline_dir, limit=download.LIMIT):
    if offline_dir is None:
        return download.https_bytes(REPOSITORY + '/releases/download/v' + version + '/' + name, limit)
    base = Path(offline_dir)
    if (base / 'mods').is_dir():base = base / 'mods'
    path = state.safe(base / name)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Missing or unsafe offline Mods asset: ' + name)
    return path.read_bytes()


def safe_members(payload):
    """Validate every member before creating even the destination directory."""
    files = {}; names = set(); size = 0
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                parts = path.parts
                if (not parts or parts[0] != 'aikya-mods' or '\\' in info.filename
                        or any(p in ('.', '..') or ':' in p or p.endswith((' ', '.'))
                               or re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?', p) for p in parts)
                        or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))):
                    raise ValueError('Unsafe Mods archive member')
                key = unicodedata.normalize('NFC', '/'.join(parts)).casefold()
                if key in names:
                    raise ValueError('Duplicate Mods archive member')
                names.add(key)
                size += info.file_size
                if size > download.LIMIT or len(names) > 10000:
                    raise ValueError('Mods archive exceeds extraction limit')
                if not info.is_dir():
                    files[path.relative_to('aikya-mods').as_posix()] = archive.read(info)
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError('Invalid Mods ZIP archive') from exc
    return files


def catalog(files, version, release):
    try:
        if files['VERSION'].decode().strip().removeprefix('v') != version or release['version'].removeprefix('v') != version:
            raise ValueError('Mods bundle version mismatch')
        market = json.loads(files['.claude-plugin/marketplace.json'])
        if market['name'] != 'aikya-mods' or not isinstance(market['plugins'], list):
            raise ValueError('Invalid official Mods marketplace')
        if not isinstance(market.get('owner'), dict) or not isinstance(market['owner'].get('name'), str) or not market['owner']['name'].strip():
            raise ValueError('Invalid marketplace owner')
        plugins = {}
        for entry in market['plugins']:
            name = entry['name']
            if (not isinstance(name, str) or not re.fullmatch(r'aikya-[a-z0-9-]+', name)
                    or name in plugins or entry['source'] != './mods/' + name):
                raise ValueError('Invalid Mods plugin source/name')
            plugin_version = download.validate_version(entry['version'])
            manifest = json.loads(files['mods/' + name + '/.claude-plugin/plugin.json'])
            if manifest['name'] != name or manifest['version'] != plugin_version:
                raise ValueError('Mods plugin manifest mismatch')
            plugins[name] = plugin_version
        if not plugins or release['mods'] != plugins:
            raise ValueError('Mods release catalog mismatch')
        minimum = download.validate_version(release['claude_version'])
        return plugins, minimum
    except (KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Malformed Mods release/catalog') from exc


def prepare_mods(version, destination, offline_dir=None):
    version = download.validate_version(version)
    hashes = download.parse_checksums(asset(version, 'SHA256SUMS', offline_dir, 128 * 1024))
    assets = {}
    for name in ('release.json', 'aikya-mods-v' + version + '.zip'):
        data = asset(version, name, offline_dir)
        if hashlib.sha256(data).hexdigest() != hashes.get(name):
            raise ValueError('Mods asset integrity checksum mismatch: ' + name)
        assets[name] = data
    try:
        release = json.loads(assets['release.json'])
        files = safe_members(assets['aikya-mods-v' + version + '.zip'])
        plugins, minimum = catalog(files, version, release)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid Mods release metadata') from exc
    return persist_files(files, version, plugins, minimum, destination)


def persist_bundle(bundle, destination):
    files = {p.relative_to(bundle.path).as_posix(): state.safe(p).read_bytes()
             for p in bundle.path.rglob("*") if p.is_file()}
    if {n: hashlib.sha256(raw).hexdigest() for n, raw in files.items()} != dict(bundle.hashes):
        raise ValueError("Prepared Mods source was modified")
    return persist_files(files, bundle.version, bundle.plugins, bundle.claude_version, destination)


def persist_files(files, version, plugins, minimum, destination):
    destination = state.safe(Path(destination))
    source = state.safe(destination / ('v' + version) / 'aikya-mods')
    record = {'schema': 1, 'version': version, 'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}}
    marker = source.parent / 'aikya-source.json'
    if source.parent.exists():
        actual = {p.relative_to(source).as_posix(): hashlib.sha256(state.safe(p).read_bytes()).hexdigest()
                  for p in source.rglob('*') if p.is_file() or p.is_symlink()}
        if not marker.is_file() or json.loads(marker.read_text(encoding='utf8')) != record or actual != record['files']:
            raise ValueError('Customized or modified Mods source requires review')
    else:
        destination.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='.mods-', dir=destination))
        try:
            for name, raw in files.items():
                path = stage / 'aikya-mods' / name
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            state.write_json(stage / 'aikya-source.json', record)
            stage.rename(source.parent)
        finally:
            if stage.exists():shutil.rmtree(stage)
    return VerifiedModsBundle(version, source, plugins, minimum, tuple(sorted(record["files"].items())))
