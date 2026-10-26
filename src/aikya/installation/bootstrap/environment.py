"""Platform storage and final-path virtual environments, without shell activation."""
import json
import os
from pathlib import Path
import subprocess
import zipfile
from email.parser import BytesParser


from .options import app_root

def run(python, *args):
    try:
        process = subprocess.run([str(python), '-I', '-B', '-X', 'utf8', *map(str, args)], capture_output=True, text=True, encoding='utf8', timeout=180)
    except subprocess.SubprocessError as exc:
        raise ValueError('Installer subprocess timed out or could not complete') from exc
    if process.returncode:
        raise ValueError('Installer subprocess failed: ' + process.stderr[-2000:] + process.stdout[-1000:])
    return process.stdout


def check_python(python):
    try:
        result = json.loads(run(python, '-c', 'import sys,json,venv,ensurepip;print(json.dumps(list(sys.version_info[:2])))'))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ValueError('A working Python 3.10–3.13 with venv/ensurepip is required') from exc
    if result not in [[3, minor] for minor in range(10, 14)]:
        raise ValueError('Python must be within the tested 3.10–3.13 range')


def verify_wheel(wheel, version):
    with zipfile.ZipFile(wheel) as archive:
        metadata = [name for name in archive.namelist() if name.endswith('.dist-info/METADATA')]
        if len(metadata) != 1:
            raise ValueError('Invalid Aikya wheel metadata')
        info = BytesParser().parsebytes(archive.read(metadata[0]))
        if info['Name'] != 'aikya-harness' or info['Version'] != version:
            raise ValueError('Wheel package/version does not match the requested release')


def create_environment(destination: Path, python: Path, wheel: Path) -> Path:
    check_python(python)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Candidate environment must have a new final path')
    run(python, '-m', 'venv', destination)
    candidate = destination / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    run(candidate, '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', wheel)
    run(candidate, '-c', "from importlib.metadata import version;from importlib.util import find_spec;import aikya;assert find_spec('claude_agent_sdk') is None;print(version('aikya-harness'))")
    return candidate
