#!/usr/bin/env python3
"""Aikya SessionStart welcome: user-visible message, no model context or network.

The Claude Code hook emits a JSON systemMessage. --preview prints the same panel
for testing or manual inspection outside Claude Code.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_SOURCE = 'https://github.com/jlema0590/aikya-harnes'
_ALLOWED_EVENTS = {'startup', 'resume', 'fork'}


def clean(value: object, fallback: str, limit: int = 100) -> str:
    """Remove terminal control characters and cap user-derived text."""
    if not isinstance(value, str):
        return fallback
    text = re.sub(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]+', ' ', value)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:limit] if text else fallback


def git_value(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ['git', '-C', str(root), *arguments],
            check=False, capture_output=True, text=True, timeout=1,
        )
        return result.stdout.strip() if result.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        return ''


def safe_remote(value: str) -> str:
    """Only expose a recognizable repository slug; never a credential-bearing URL."""
    if not value or any(char in value for char in '\r\n\x1b'):
        return ''
    value = value.strip()
    if value.startswith('git@github.com:'):
        path = value.split(':', 1)[1]
    elif value.startswith('ssh://git@github.com/'):
        path = value[len('ssh://git@github.com/'):]
    else:
        parsed = urlparse(value)
        if parsed.hostname != 'github.com' or parsed.scheme not in ('https', 'http'):
            return ''
        path = parsed.path.lstrip('/')
    path = path.removesuffix('.git').strip('/')
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', path):
        return path
    return ''


def identity(root: Path) -> str:
    env = os.environ.get('AIKYA_DISPLAY_NAME', '')
    if env.strip():
        return clean(env, 'Desarrollador', 48)
    try:
        local = json.loads((root / '.harness/welcome.json').read_text(encoding='utf8'))
        if isinstance(local, dict) and local.get('display_name'):
            return clean(local['display_name'], 'Desarrollador', 48)
    except (OSError, UnicodeError, ValueError):
        pass
    # Git config is per developer; do not commit a personal name into the template.
    configured = git_value(root, 'config', '--get', 'user.name')
    if configured:
        return clean(configured, 'Desarrollador', 48)
    return 'Desarrollador'


def repository(root: Path) -> str:
    remote = safe_remote(git_value(root, 'remote', 'get-url', 'origin'))
    return clean(remote, clean(root.name, 'proyecto', 60), 64)


def build_message(root: Path) -> str:
    who = identity(root)
    repo = repository(root)
    # Short box: CLI notification renderers may not support ANSI or wide panels.
    lines = [
        '================================== Welcome to Aikya Harness ==================================',
        f'Developer: {who}',
        f'Repository: {repo}',
        f'Aikya project: {DEFAULT_SOURCE}',
        'Commands start: /aikya-init · /aikya-analyze · /aikya-doctor · /aikya-answers',
        'Commands develop: /aikya-scaffold · /aikya-feature · /aikya-bugfix  · /aikya-quality',
        'Commands arquitecture: //aikya-arc-review',
        'Commands mobile: /aikya-mobile-feature',
        'Commands test: /aikya-test',
        'Project documentation: aikya/docs/README.md',
        '==============================================================================================',
    ]
    width = min(max(len(line) for line in lines), 95)
    border = '+' + '-' * (width + 2) + '+'
    return '\n'.join([border, *('| ' + line.ljust(width) + ' |' for line in lines), border])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Aikya Harness welcome message')
    parser.add_argument('--preview', action='store_true', help='Preview the welcome without starting Claude Code')
    parser.add_argument('--project-root', type=Path, help='Repository directory (preview/tests)')
    args = parser.parse_args(argv)
    root = (args.project_root or Path(os.environ.get('CLAUDE_PROJECT_DIR') or Path(__file__).resolve().parents[2])).resolve()
    if args.preview:
        print(build_message(root))
        return 0
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    # Only greet at session entry; not on /clear or context compaction.
    if isinstance(payload, dict) and payload.get('source', 'startup') not in _ALLOWED_EVENTS:
        return 0
    print(json.dumps({'systemMessage': build_message(root)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
