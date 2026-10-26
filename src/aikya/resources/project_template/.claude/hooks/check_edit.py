#!/usr/bin/env python3
"""Analiza sintaxis de un archivo Python o JSON justo después de Edit/Write.

Solo aporta feedback; no sustituye lint ni tests.
"""
import ast
import json
import os
from pathlib import Path
import sys


def feedback(event, project_root):
    value = event.get('tool_input', {}).get('file_path')
    if not value or not isinstance(value, str):
        return None
    file = Path(value)
    if not file.is_absolute():
        file = Path(project_root) / file
    file = file.resolve()
    root = Path(project_root).resolve()
    try:
        file.relative_to(root)
    except ValueError:
        return None
    if not file.is_file():
        return None
    runtime=root/'aikya/scripts/harness'
    if runtime.is_dir():sys.path.insert(0,str(runtime))
    try:
        from code_quality import inspect_paths
        report=inspect_paths(root,[file.relative_to(root).as_posix()])
        findings=report['errors']+report['warnings']
        if findings:return 'Code quality: '+json.dumps(findings,ensure_ascii=False)
    except ImportError:pass
    except (ValueError,OSError) as exc:return 'Code quality NOT VERIFIED: '+str(exc)
    if file.suffix not in {'.py','.json'}:return None
    try:
        source = file.read_text(encoding='utf-8')
        if file.suffix == '.py':
            ast.parse(source, filename=str(file))
        else:
            json.loads(source)
    except (SyntaxError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return f'ATENCIÓN: sintaxis inválida en {file.relative_to(root)}: {exc}'
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    project_root = os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or '.'
    msg = feedback(event, project_root)
    if msg:
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'PostToolUse', 'additionalContext': msg
        }}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
