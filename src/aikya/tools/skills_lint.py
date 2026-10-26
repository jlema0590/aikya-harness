#!/usr/bin/env python3
"""Validador básico sin dependencias de la estructura Agent Skills.

No sustituye `skills-ref validate` oficial; chequea el subset usado por el harness.
"""
from __future__ import annotations
from aikya.resource_paths import project_root
import argparse
import re
from pathlib import Path

NAME = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def inspect_skill(path: Path) -> list[str]:
    issues=[]
    try:
        txt = path.read_text(encoding='utf8')
    except (UnicodeError,OSError):
        return [f'{path}: no se pudo leer SKILL.md']
    if not txt.startswith('---\n'):
        return [f'{path}: falta YAML frontmatter al inicio']
    parts = txt.split('---\n',2)
    if len(parts) < 3:
        return [f'{path}: frontmatter sin cierre']
    head = parts[1]
    fields={}
    for line in head.splitlines():
        match = re.match(r'^([a-z][a-z0-9-]*):\s*(.*)$',line)
        if match:
            fields[match.group(1)] = match.group(2).strip(' "\'')
    name, desc=fields.get('name',''),fields.get('description','')
    if not NAME.fullmatch(name) or not 1 <= len(name) <= 64 or name != path.parent.name:
        issues.append(f'{path}: name inválido o no coincide con directorio')
    if not 1 <= len(desc) <= 1024:
        issues.append(f'{path}: description ausente o fuera de rango')
    if 'compatibility' in fields and len(fields['compatibility'])>500:
        issues.append(f'{path}: compatibility >500 caracteres')
    if len(parts[2].splitlines()) > 500:
        issues.append(f'{path}: SKILL.md tiene >500 líneas, mueve detalles a references/')
    if not parts[2].strip():
        issues.append(f'{path}: instrucciones vacías')
    return issues


def validate(root: Path, include_vendor: bool = False) -> list[str]:
    base = root/'.claude/skills'
    if not base.exists():
        return [f'{base}: no existe directorio de skills']
    errors=[]
    skills=[s for s in base.iterdir() if s.is_dir()]
    if not skills:
        return [f'{base}: no hay skills']
    for skill in sorted(skills):
        if not include_vendor and skill.name in ('ponytail','graphify','ui-ux-pro-max'):
            continue  # externos se validan por su cadena de suministro upstream
        errors += inspect_skill(skill/'SKILL.md')
    return errors


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=project_root())
    parser.add_argument('--include-vendor',action='store_true')
    args=parser.parse_args()
    errors=validate(args.root.resolve(),args.include_vendor)
    print('\n'.join(errors) if errors else 'Skills locales: formato Agent Skills válido (comprobaciones básicas).')
    return bool(errors)

if __name__=='__main__':
    raise SystemExit(main())
