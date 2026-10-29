"""Build deterministic platform installers with pinned bootstrap integrity."""
import argparse
import hashlib
from pathlib import Path
import re
import shlex
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def build(version, output, parser_wheels=None):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('An explicit numeric version is required')
    output.mkdir(parents=True, exist_ok=True)
    if parser_wheels is not None:
        import shutil
        for wheel in sorted(Path(parser_wheels).glob('tree_sitter*.whl')):
            if wheel.is_symlink():raise ValueError('Symlinked parser wheel')
            shutil.copyfile(wheel, output/wheel.name)
    source = ROOT / 'src/aikya/installation/bootstrap'
    entries = {'__main__.py': b'from bootstrap.cli import main\nraise SystemExit(main())\n'}
    entries.update({'bootstrap/' + p.name: p.read_bytes() for p in sorted(source.glob('*.py'))})
    payload = output / 'aikya-bootstrap.pyz'
    with zipfile.ZipFile(payload, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    for name in ('install.sh', 'install.ps1'):
        text = (ROOT / 'scripts/install' / (name + '.tmpl')).read_text(encoding='utf8')
        text = text.replace('@@VERSION@@', version).replace('@@BOOTSTRAP_SHA256@@', digest)
        preview = (source / 'options.py').read_text(encoding='utf8') + '\nraise SystemExit(entry_preview())\n'
        text = text.replace('@@PREVIEW_SHELL@@', shlex.quote(preview)).replace('@@PREVIEW_CODE@@', preview)
        if '@@' in text:
            raise ValueError('Unresolved installer template placeholder')
        (output / name).write_text(text, encoding='utf8')
    (output / 'install.sh').chmod(0o755)
    assets = [p for p in sorted(output.iterdir()) if p.is_file() and (p.name in ('aikya-bootstrap.pyz', 'install.sh', 'install.ps1') or p.name.endswith(('.whl', '.tar.gz', '.zip')))]
    (output / 'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in assets))
    return [p.name for p in assets]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--parser-wheels', type=Path, help='Reviewed pinned binary wheel directory for release/offline assets')
    args = parser.parse_args()
    print('\n'.join(build(args.version, args.output.resolve(), args.parser_wheels)))


if __name__ == '__main__':
    main()
