"""Validate immutable installer release sets and recover only missing exact assets."""
import argparse
import hashlib
from pathlib import Path
import re
from aikya.installation.bootstrap.environment import verify_wheel


def verify_assets(directory, version):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Invalid release version')
    names = {'aikya_harness-' + version + '-py3-none-any.whl', 'aikya_harness-' + version + '.tar.gz',
             'aikya-harness-v' + version + '.zip', 'aikya-bootstrap.pyz', 'install.sh', 'install.ps1'}
    from aikya.installation.bootstrap.code_index import PINS
    def parser_asset(name):
        return any(name.startswith(k.replace('-','_')+'-'+v+'-') and name.endswith('.whl') for k,v in PINS.items())
    entries = {}
    for line in (directory / 'SHA256SUMS').read_text(encoding='ascii').splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9_.-]+)', line)
        if not match or match[2] in entries or (match[2] not in names and not parser_asset(match[2])):
            raise ValueError('Invalid release manifest entry')
        entries[match[2]] = match[1]
    if not names<=set(entries):
        raise ValueError('Incomplete installer release manifest')
    for name, digest in entries.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Invalid release asset: ' + name)
    verify_wheel(directory / ('aikya_harness-' + version + '-py3-none-any.whl'), version)
    return sorted(entries) + ['SHA256SUMS']


def compare_assets(candidate, existing, version):
    names = verify_assets(candidate, version)
    missing = []
    for name in names:
        remote = existing / name
        if not remote.exists():
            missing.append(name)
        elif remote.is_symlink() or remote.read_bytes() != (candidate / name).read_bytes():
            raise ValueError('Published release asset conflicts; never overwrite: ' + name)
    return missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--existing', type=Path)
    args = parser.parse_args()
    names = compare_assets(args.directory, args.existing, args.version) if args.existing else verify_assets(args.directory, args.version)
    print('\n'.join(names))


if __name__ == '__main__':
    main()
