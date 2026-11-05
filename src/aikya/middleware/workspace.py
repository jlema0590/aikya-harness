"""Require explicit host permission for worktree creation; never creates one."""
import json
from pathlib import Path
import shlex
import sys

INSTRUCTION = ('Work in the current checkout. Create a worktree only when the user '
               'explicitly requests one; a branch request does not authorize a worktree.')
MATCHER = 'Bash|PowerShell|Agent|Task|EnterWorktree'


def creates_worktree(command):
    if not isinstance(command, str):
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()\n')
        lexer.whitespace = ' \t\r'
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False  # Malformed shell input remains subject to the host's policy.
    segments = [[]]
    for token in tokens:
        if token and all(c in ';&|()\n' for c in token):
            segments.append([])
        else:
            segments[-1].append(token)
    for words in segments:
        while words and ('=' in words[0] or words[0] in ('env', 'command', 'exec', 'sudo')):
            words = words[1:]
        if not words:
            continue
        executable = words[0].replace('\\', '/').rsplit('/', 1)[-1].lower()
        args = [word.lower() for word in words[1:]]
        if executable in ('git', 'git.exe'):
            if any(args[i:i + 2] == ['worktree', 'add'] for i in range(len(args) - 1)):
                return True
        if executable in ('claude', 'claude.exe') and any(
                a in ('--worktree', '-w') or a.startswith('--worktree=') for a in args):
            return True
    return False


def decision(event):
    tool = event.get('tool_name')
    inputs = event.get('tool_input', {})
    if not isinstance(inputs, dict):
        return None
    requested = (tool == 'EnterWorktree' or
                 tool in ('Agent', 'Task') and inputs.get('isolation') == 'worktree' or
                 tool in ('Bash', 'PowerShell') and creates_worktree(inputs.get('command')))
    if requested:
        return {'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                'permissionDecision': 'ask', 'permissionDecisionReason': INSTRUCTION}}
    return None


def register(settings, command, logs):
    from aikya.storage import atomic_write
    settings = Path(settings)
    if any(p.is_symlink() for p in (settings, *settings.parents)):
        logs.append('NEEDS_REVIEW workspace policy settings path preserved')
        return
    try:
        data = json.loads(settings.read_text()) if settings.exists() else {}
        if not isinstance(data, dict) or not isinstance(data.get('hooks', {}), dict):
            raise ValueError('Invalid custom hooks')
        groups = data.setdefault('hooks', {}).setdefault('PreToolUse', [])
        if not isinstance(groups, list):
            raise ValueError('Invalid custom PreToolUse groups')
        if any(isinstance(g, dict) and g.get('matcher') == MATCHER and command in g.get('hooks', []) for g in groups):
            return
        groups.append({'matcher': MATCHER, 'hooks': [command]})
    except (ValueError, OSError, TypeError):
        logs.append('NEEDS_REVIEW custom workspace settings preserved')
        return
    atomic_write(settings, json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    logs.append('REGISTERED explicit-worktree permission policy: ' + str(settings))


def main():
    try:
        event = json.load(sys.stdin)
        result = decision(event) if isinstance(event, dict) else None
        if result:
            print(json.dumps(result))
        return 0
    except (ValueError, OSError, TypeError):
        print('NOTICE: workspace hook input unavailable; host permissions remain authoritative.', file=sys.stderr)
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
