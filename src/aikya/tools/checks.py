#!/usr/bin/env python3
"""Ejecuta comandos configurados de verificación sin lanzar un shell.

`required` + comando nulo => fallo: no confundir 'sin configurar' con 'pasó'.
"""
from aikya.resource_paths import project_root
import json
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import subprocess
import sys

ROOT = project_root()
CONFIG = ROOT / 'harness.json'


def run(config_path=CONFIG):
    try:
        config = json.loads(Path(config_path).read_text(encoding='utf-8'))
        checks = config['checks']
        if not isinstance(checks, list) or not checks:
            raise ValueError('checks debe ser una lista no vacía')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR configuración: {exc}')
        return 2

    from aikya.tools.check_evidence import binding, reusable, previous
    prior_evidence=previous(ROOT)
    try:
        from aikya.middleware.events import CheckEvents
        observer=CheckEvents(ROOT)
    except ImportError:observer=None
    failures = 0
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get('name'), str) or not isinstance(check.get('required'), bool):
            print(f'ERROR check mal definido: {check!r}')
            failures += 1
            continue
        name, cmd, required = check['name'], check.get('command'), check['required']
        workdir = check.get('cwd', '.')
        if not isinstance(workdir, str) or not workdir:
            print(f'{name}: INVALID_CWD (debe ser ruta relativa no vacía)')
            failures += 1
            continue
        try:
            cwd = (ROOT / workdir).resolve()
            cwd.relative_to(ROOT.resolve())
            if not cwd.is_dir():
                raise ValueError('directorio inexistente')
        except ValueError:
            print(f'{name}: INVALID_CWD (fuera del repositorio o inexistente)')
            failures += 1
            continue
        if cmd is None:
            print(f'{name}: NOT_CONFIGURED' + (' [OBLIGATORIO]' if required else ' [opcional]'))
            failures += int(required)
            continue
        if not isinstance(cmd, list) or not cmd or any(not isinstance(arg, str) or not arg for arg in cmd):
            print(f'{name}: INVALID_COMMAND (se espera array de cadenas no vacías)')
            failures += 1
            continue
        managed = {
            'docs:structure': ['python3', 'aikya/scripts/harness/docs_guard.py', 'base'],
            'skills:format': ['python3', 'aikya/scripts/harness/skills_lint.py'],
            'infra:static': ['python3', 'aikya/scripts/harness/infrastructure.py', 'validate'],
            'sdd:traceability': ['python3', 'aikya/scripts/harness/sdd_engine.py', 'lint', '--root', '.'],
        }
        if cmd == managed.get(name):
            cmd = [sys.executable, *cmd[1:]]
        candidate_binding=binding(ROOT,check)
        if any(e.get('check')==name and reusable(e,candidate_binding) for e in prior_evidence):
            if observer:observer.process(name,0,candidate_binding)
            print(f'{name}: PASSED (reused matching deterministic evidence)')
            continue
        print(f'{name}: RUNNING {cmd!r}', flush=True)
        try:
            result = subprocess.run(cmd, cwd=cwd, check=False, timeout=300)
            if observer:observer.process(name,result.returncode,candidate_binding if binding(ROOT,check)==candidate_binding else None)
            if result.returncode != 0:
                print(f'{name}: FAILED (exit {result.returncode})')
                failures += 1
            else:
                print(f'{name}: PASSED')
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'{name}: FAILED ({exc})')
            failures += 1
    if observer:observer.finish(failures)
    print(f'RESULTADO: {"FAILED" if failures else "PASSED"} ({failures} check(s) pendientes/fallidos)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(run())
