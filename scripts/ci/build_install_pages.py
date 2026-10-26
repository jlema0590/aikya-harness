"""Publish exact checksum-verified entry assets from an already published release."""
import argparse
import hashlib
import json
from pathlib import Path
from aikya.installation.bootstrap import download
from aikya.installation.bootstrap.options import MIN_UNIFIED_VERSION


def build(version, assets, output):
    version=download.validate_version(version)
    if tuple(map(int,version.split('.'))) < MIN_UNIFIED_VERSION:
        raise ValueError('Unified installation pages require Harness 7.1.0 or newer')
    hashes=download.parse_checksums((assets/'SHA256SUMS').read_bytes())
    scripts={}
    for name in ('install.sh','install.ps1'):
        path=assets/name
        if path.is_symlink() or not path.is_file():raise ValueError('Missing safe installer asset')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=hashes.get(name):raise ValueError('Installer integrity checksum mismatch')
        scripts[name]=raw
    if output.exists():raise ValueError('Pages output must be a new directory')
    output.mkdir(parents=True)
    (output/'install.sh').write_bytes(scripts['install.sh'])
    (output/'install.ps1.txt').write_bytes(scripts['install.ps1'])
    (output/'.nojekyll').write_bytes(b'')
    provenance={'tag':'v'+version,'source':download.REPOSITORY+'/releases/tag/v'+version,
                'sha256':{name:hashes[name] for name in scripts}}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8')
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Aikya installation</title>'
        '<h1>Aikya Harness</h1><p>Requires Python 3.10–3.13 with venv/pip and Claude Code 2.1.308+ for Mods.</p>'
        '<h2>Linux / macOS</h2><pre>curl -fsSL https://jlema0590.github.io/aikya-harness/install.sh | sh</pre>'
        '<h2>Windows PowerShell</h2><pre>irm https://jlema0590.github.io/aikya-harness/install.ps1.txt | iex</pre>'
        '<p>Default: global Harness + Flow + Usage. BoxBot: --mods all. Restart your terminal and Claude.</p>'
        '<p><a href="install.sh">Inspect shell installer</a> · <a href="install.ps1.txt">Inspect PowerShell installer</a> · '
        '<a href="provenance.json">Release provenance</a> · '
        '<a href="https://github.com/jlema0590/aikya-harness#1-quick-start">Options and updates</a></p></html>\n',encoding='utf8')
    return provenance


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.version,args.assets,args.output),indent=2))
