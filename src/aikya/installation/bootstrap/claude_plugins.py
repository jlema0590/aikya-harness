"""Native Claude plugin operations, without shell commands or model calls."""
import json
from pathlib import Path
import re
import shutil
import subprocess


class Claude:
    def __init__(self, target=None):
        self.cwd = Path(target or Path.cwd()).resolve()
        self.executable = shutil.which('claude')
        if not self.executable:
            raise ValueError('Claude Code with native plugin support is required; use --mods none for Harness only')
        if Path(self.executable).suffix.lower() in ('.cmd', '.bat'):
            raise ValueError('Use the native Claude executable on Windows, not a shell wrapper')

    def run(self, *args):
        try:
            result = subprocess.run([self.executable, *map(str, args)], cwd=self.cwd,
                                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('Claude plugin command could not complete') from exc
        if result.returncode:
            raise ValueError('Claude plugin command failed: ' + result.stdout[-1500:] + result.stderr[-1500:])
        if len(result.stdout) > 2 * 1024 * 1024:
            raise ValueError('Claude plugin response exceeds limit')
        return result.stdout

    def preflight(self, minimum='2.1.308'):
        found = re.search(r'\b(\d+\.\d+\.\d+)\b', self.run('--version'))
        required = max(tuple(map(int, minimum.split('.'))), (2, 1, 308))
        if not found or tuple(map(int, found[1].split('.'))) < required:
            raise ValueError('Claude Code ' + '.'.join(map(str, required)) + ' or newer is required for Mods')
        for args in (('plugin','install'), ('plugin','update'), ('plugin','uninstall'), ('plugin','marketplace','add'), ('plugin','marketplace','remove')):
            if '--json' not in self.run(*args, '--help'):
                raise ValueError('Claude CLI lacks required JSON plugin capabilities')
        self.inventory(); self.marketplaces()

    def command(self, *args):
        raw = self.run(*args)
        try:
            result = json.loads(raw.strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise ValueError('Invalid Claude plugin JSON result') from exc
        if not isinstance(result, dict) or result.get('outcome') != 'ok':
            raise ValueError('Claude plugin operation did not report success')
        return result

    def listing(self, *args):
        try:
            records = json.loads(self.run(*args, '--json'))
        except ValueError as exc:
            raise ValueError('Invalid Claude inventory JSON') from exc
        if not isinstance(records, list) or any(not isinstance(p, dict) for p in records):
            raise ValueError('Invalid Claude inventory schema')
        return records

    def inventory(self):
        return self.listing('plugin', 'list')

    def marketplaces(self):
        return self.listing('plugin', 'marketplace', 'list')
