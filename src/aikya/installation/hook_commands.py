"""Literal managed-interpreter commands for POSIX shells and native PowerShell."""
import base64
import copy
import os
from pathlib import Path
import re
import shlex
import sys


def host_shell():
    return 'powershell' if os.name == 'nt' else 'posix'


def render_managed_hook(python: Path, script: Path, args: tuple[str, ...], shell: str) -> dict:
    if not python.is_absolute() or not script.is_absolute():
        raise ValueError('Managed hooks require absolute interpreter and script paths')
    tokens = [str(python), '-B', str(script), *args]
    record = {'type': 'command', 'timeout': 5}
    if shell == 'posix':
        record['command'] = shlex.join(tokens)
    elif shell == 'powershell':
        record['command'] = '& ' + ' '.join("'" + token.replace("'", "''") + "'" for token in tokens)
        record['shell'] = 'powershell'
    else:
        raise ValueError('Unsupported hook shell')
    return record


def status_command(python, script, shell=None):
    shell = shell or host_shell()
    command = render_managed_hook(python, script, (), shell)['command']
    if shell == 'powershell':
        # Statusline has no hook shell field; this also runs through Git Bash.
        payload = base64.b64encode(command.encode('utf-16-le')).decode('ascii')
        return 'powershell -NoProfile -NonInteractive -EncodedCommand ' + payload
    return command


def project_settings(source, target):
    settings = copy.deepcopy(source)
    for groups in settings.get('hooks', {}).values():
        for group in groups:
            if os.name == 'nt' and group.get('matcher') == 'Bash':
                group['matcher'] = 'Bash|PowerShell'
            for hook in group.get('hooks', []):
                command = hook.get('command', '')
                match = re.search(r'\$\{CLAUDE_PROJECT_DIR\}/([^"\s]+\.py)', command)
                if not match:
                    continue
                replacement = render_managed_hook(Path(sys.executable).absolute(), target / match[1], (), host_shell())
                hook.update(replacement)
    return settings
