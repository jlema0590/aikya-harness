"""Run regression fixtures without reading the contributor's personal Claude settings.

Only the child test process receives a temporary home and storage directories.
The caller's environment, installed tools and project configuration are unchanged.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', default='test_*.py')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='aikya-regression-') as task_directory:
        task_home = Path(task_directory).resolve()
        task_env = dict(os.environ)
        task_env.update({
            'HOME': str(task_home), 'USERPROFILE': str(task_home),
            'APPDATA': str(task_home / 'AppData/Roaming'),
            'LOCALAPPDATA': str(task_home / 'AppData/Local'),
            'XDG_STATE_HOME': str(task_home / '.local/state'),
            'XDG_CACHE_HOME': str(task_home / '.cache'),
            'CLAUDE_CONFIG_DIR': str(task_home / '.claude'),
            'AIKYA_EXECUTION_CACHE': str(task_home / 'execution'),
            'PYTHONDONTWRITEBYTECODE': '1',
        })
        for name in ('AIKYA_FLOW_CONTEXT', 'CLAUDE_SESSION_ID', 'CLAUDE_PROJECT_DIR', 'AIKYA_INSTALL_ROOT', 'PYTHONPATH'):
            task_env.pop(name, None)
        return subprocess.call([sys.executable, '-B', '-m', 'unittest', 'discover',
                                '-s', 'tests', '-p', args.pattern, '-v'], cwd=root, env=task_env)


if __name__ == '__main__':
    raise SystemExit(main())
