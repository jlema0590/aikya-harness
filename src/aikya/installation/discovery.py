"""Focused installer discovery responsibilities."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from aikya.installation.defaults import CANDIDATE_DIRS


def root_directories(root: Path) -> list[Path]:
    return [p for rel in CANDIDATE_DIRS if (p := root / rel).is_dir()]



def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix() or '.'



def read_json_safe(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf8'))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeError, ValueError):
        return {}



def detect_project(root: Path) -> dict[str, Any]:
    """Conservative manifest/name-based detection that never executes commands."""
    modules: list[dict[str, Any]] = []
    findings: list[str] = []
    seen: set[tuple[str, str, str]] = set()

    def add(role: str, technology: str, folder: Path, detail: str = '') -> None:
        key = (role, technology, relative(root, folder))
        if key not in seen:
            seen.add(key)
            modules.append({'role': role, 'technology': technology, 'path': key[2]})
            findings.append(f'{technology} ({role}) en {key[2]}' + (f' — {detail}' if detail else ''))

    for folder in root_directories(root):
        pkgpath = folder / 'package.json'
        if pkgpath.is_file():
            pkg = read_json_safe(pkgpath)
            declared = pkg.get('dependencies') or {}
            dev = pkg.get('devDependencies') or {}
            deps = {**(declared if isinstance(declared, dict) else {}), **(dev if isinstance(dev, dict) else {})}
            if '@angular/core' in deps:
                add('frontend', 'angular', folder)
            if 'next' in deps:
                add('backend', 'next', folder, 'Next.js, puede ser full-stack')
                add('frontend', 'react', folder, 'integrado en Next.js')
            elif any(k in deps for k in ('react-native', 'expo')):
                add('mobile', 'react-native', folder)
            else:
                if any(k in deps for k in ('express', 'fastify', '@nestjs/core', 'koa', 'hono')):
                    add('backend', 'node', folder)
                if 'react' in deps:
                    add('frontend', 'react', folder)
                if 'vue' in deps or 'nuxt' in deps:
                    add('frontend', 'vue', folder)
            if not deps:
                findings.append(f'package.json encontrado en {relative(root, folder)} (framework desconocido)')
        if (folder / 'pyproject.toml').is_file() or (folder / 'requirements.txt').is_file():
            add('backend', 'python', folder, 'Verificar framework y entorno virtual')
        if (folder / 'pom.xml').exists():
            add('backend', 'java', folder, 'Maven; confirm actual application type')
        if (folder / 'build.gradle').exists() or (folder / 'build.gradle.kts').exists():
            is_android = (folder / 'app/src/main/AndroidManifest.xml').exists() or (folder / 'src/main/AndroidManifest.xml').exists()
            if is_android:
                add('mobile', 'android', folder)
            elif not (folder / 'pom.xml').exists():
                add('backend', 'java', folder, 'Gradle; confirm actual application type')
        if (folder / 'app/src/main/AndroidManifest.xml').exists():
            add('mobile', 'android', folder)
        for project in sorted(folder.glob('*.csproj'))[:5]:
            add('backend', 'dotnet', folder, project.name)
        if any(folder.glob('*.xcodeproj')) or any(folder.glob('*.xcworkspace')):
            add('mobile', 'ios', folder)
        if (folder / 'pubspec.yaml').exists():
            add('mobile', 'flutter', folder)
    if not modules:
        findings.append('No se pudo identificar un framework con suficiente confianza.')
    return {'modules': modules, 'findings': findings}
