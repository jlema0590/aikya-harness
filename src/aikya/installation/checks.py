"""Focused installer checks responsibilities."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any
from aikya.installation.defaults import PACKAGES
from aikya.installation.discovery import read_json_safe


def package_command(manager: str, script: str) -> list[str]:
    return {'npm': ['npm','run',script], 'pnpm':['pnpm','run',script],
            'yarn':['yarn',script], 'bun':['bun','run',script]}[manager]



def manager_for(folder: Path, fallback: str) -> str:
    if (folder / 'pnpm-lock.yaml').exists():
        return 'pnpm'
    if (folder / 'yarn.lock').exists():
        return 'yarn'
    if (folder / 'bun.lockb').exists() or (folder / 'bun.lock').exists():
        return 'bun'
    if (folder / 'package-lock.json').exists():
        return 'npm'
    return fallback if fallback in PACKAGES else 'npm'



def make_checks(root: Path, profile: dict[str, Any], modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """No inventar comandos sin manifiesto ni tests sin scripts."""
    checks: list[dict[str, Any]] = []
    def add(name: str, command: list[str] | None, cwd: str='.', required: bool=False) -> None:
        if not any(x['name'] == name for x in checks):
            checks.append({'name': name, 'command': command, 'cwd': cwd, 'required': required})
    if profile.get('project_type','development')!='development':
        return checks
    if profile['mode'] == 'new':
        roles=[('backend',profile['backend']), ('frontend', profile['frontend'])]
        if profile['mobile']=='both':
            roles.extend([('android','android'),('ios','ios')])
        else:
            roles.append(('mobile',profile['mobile']))
        for role, name in roles:
            if role == 'frontend' and profile['backend'] == 'next' and name == 'react':
                continue  # React pertenece a Next; un solo proyecto y set de gates
            if name != 'none':
                add(f'{role}:test', None, required=True)
                add(f'{role}:lint', None)
                add(f'{role}:build', None)
        return checks

    for module in modules:
        if module['role'] == 'frontend' and module['technology'] == 'react' and any(
            m['role'] == 'backend' and m['technology'] == 'next' and m['path'] == module['path'] for m in modules):
            continue  # Next.js y React integrado: evitar ejecutar dos veces los mismos scripts
        folder = root / module['path']
        role, tech = module['role'], module['technology']
        suffix = f'{role}:{tech}:{module["path"]}'
        if (folder / 'package.json').exists() and tech in ('node','next','react','vue','angular','react-native'):
            pkg = read_json_safe(folder / 'package.json')
            scripts = pkg.get('scripts') or {}
            scripts = scripts if isinstance(scripts, dict) else {}
            manager = manager_for(folder, profile['package_manager'])
            for task in ('lint','test','build','typecheck'):
                content = scripts.get(task)
                supported = isinstance(content, str) and 'no test specified' not in content.lower()
                add(f'{suffix}:{task}', package_command(manager,task) if supported else None,
                    module['path'], required=(task=='test'))
        elif tech == 'java':
            if (folder / 'pom.xml').exists():
                launcher = './mvnw' if (folder / 'mvnw').exists() else 'mvn'
                add(f'{suffix}:test', [launcher,'test'], module['path'], True)
                add(f'{suffix}:build', [launcher,'-DskipTests','package'], module['path'])
            elif (folder / 'gradlew').exists():
                add(f'{suffix}:test', ['./gradlew','test'], module['path'], True)
                add(f'{suffix}:build', ['./gradlew','build'], module['path'])
            else:
                add(f'{suffix}:test', None, module['path'], True)
        elif tech == 'python':
            # Only run pytest when configured in a known project manifest.
            if (folder / 'pytest.ini').is_file() or (folder / 'pyproject.toml').is_file():
                add(f'{suffix}:test', [sys.executable,'-m','pytest'], module['path'], True)
            else:
                add(f'{suffix}:test', None, module['path'], True)
        elif tech == 'dotnet':
            projects = sorted(folder.glob('*.csproj'))
            target = [projects[0].name] if len(projects) == 1 else []
            add(f'{suffix}:test', ['dotnet','test',*target], module['path'], True)
            add(f'{suffix}:build', ['dotnet','build',*target], module['path'])
        else:
            # Android/iOS: son necesarias variantes/schemes/simulador reales.
            add(f'{suffix}:test', None, module['path'], True)
            add(f'{suffix}:build', None, module['path'])
    if not checks:
        add('project:test', None, required=True)
    return checks
