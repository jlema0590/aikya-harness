"""Prepare reviewed binary-only release assets for supported CPython platforms."""
import argparse
from pathlib import Path
import subprocess
import sys
from aikya.installation.bootstrap.code_index import requirements

PLATFORMS=('manylinux2014_x86_64','manylinux2014_aarch64','musllinux_1_2_x86_64',
           'macosx_11_0_arm64','macosx_11_0_x86_64','win_amd64')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--platform',action='append',choices=PLATFORMS)
    parser.add_argument('--python-version',action='append',choices=('310','311','312','313'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    for platform in args.platform or PLATFORMS:
        for version in args.python_version or ('310','311','312','313'):
            subprocess.run([sys.executable,'-m','pip','--isolated','download','--index-url','https://pypi.org/simple',
                '--only-binary=:all:','--no-deps','--platform',platform,'--python-version',version,
                '--implementation','cp','--abi','cp'+version,'--abi','abi3','--abi','none',
                '--dest',str(args.output),*requirements('all')],check=True)
    import json
    (args.output/'parser-platforms.json').write_text(json.dumps({'supported':list(args.platform or PLATFORMS),'python':list(args.python_version or ('310','311','312','313')), 'unavailable':{'musllinux_aarch64':'No tree-sitter 0.25.2 binary; inventory fallback','windows_arm64':'Not verified; inventory fallback'}},indent=2)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
