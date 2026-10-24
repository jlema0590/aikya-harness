"""Bounded release downloads and strict SHA-256 manifests; no package indexes."""
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

REPOSITORY = 'https://github.com/jlema0590/aikya-harness'
HOSTS = {'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}
LIMIT = 100 * 1024 * 1024


def validate_version(version):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Select an explicit numeric release version, for example 7.0.0')
    return version


def validate_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
        raise ValueError('Untrusted release download URL')


class ReleaseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def https_bytes(url, limit=LIMIT):
    validate_url(url)
    with build_opener(ReleaseRedirects()).open(url, timeout=30) as response:
        validate_url(response.url)
        raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Release asset exceeds download limit')
    return raw


def parse_checksums(raw):
    if len(raw) > 128 * 1024:
        raise ValueError('Release checksum manifest is too large')
    result = {}
    for line in raw.decode('ascii').splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9][A-Za-z0-9_.-]*)', line)
        if not match or match[2] in result or '..' in match[2]:
            raise ValueError('Malformed or duplicate release checksum entry')
        result[match[2]] = match[1]
    if not result:
        raise ValueError('Empty release checksum manifest')
    return result


def fetch_release(version: str, destination: Path, offline_dir: Path | None = None) -> dict[str, Path]:
    version = validate_version(version)
    base_url = REPOSITORY + '/releases/download/v' + version + '/'
    name = 'aikya_harness-' + version + '-py3-none-any.whl'
    def read(filename, limit=LIMIT):
        if offline_dir is None:
            return https_bytes(base_url + filename, limit)
        path = Path(offline_dir) / filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
            raise ValueError('Missing or unsafe offline release asset: ' + filename)
        return path.read_bytes()
    manifest = read('SHA256SUMS', 128 * 1024)
    hashes = parse_checksums(manifest)
    if name not in hashes:
        raise ValueError('Release checksum manifest does not cover the wheel')
    payload = read(name)
    if hashlib.sha256(payload).hexdigest() != hashes[name]:
        raise ValueError('Release wheel integrity checksum mismatch')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / name
    if path.exists() or path.is_symlink():
        raise ValueError('Download destination already exists')
    path.write_bytes(payload)
    return {'wheel': path}
