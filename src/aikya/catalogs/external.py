#!/usr/bin/env python3
"""Integraciones de Agent Skills externas para Claude Code (sin MCP).

No se descargan ni ejecutan programas sin consentimiento de la persona que instala.
Integrations never modify existing user files or install dependencies through hooks.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from aikya.catalogs.skills import write_inventory

SOURCES = {
    'ponytail': 'https://github.com/DietrichGebert/ponytail.git',
    'graphify': 'https://github.com/Graphify-Labs/graphify.git',
    'ui-ux-pro-max': 'https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git',
}


def enabled_names(profile: dict[str, Any]) -> list[str]:
    names = ['ponytail', 'graphify']
    if profile.get('frontend') not in ('none', None) or profile.get('mobile') not in ('none', None):
        names.append('ui-ux-pro-max')
    return names


def planned_commands(profile: dict[str, Any]) -> list[str]:
    commands = [
        'git clone --depth 1 https://github.com/DietrichGebert/ponytail.git <carpeta-temporal>; copiar exclusivamente skills/ponytail/ -> .claude/skills/ponytail/',
        'uv tool install graphifyy  (alternativa: pipx install graphifyy)',
        'graphify install --project --platform claude',
    ]
    if 'ui-ux-pro-max' in enabled_names(profile):
        commands.append('npx --yes ui-ux-pro-max-cli init --ai claude')
    return commands


def _invoke(argv: list[str], *, cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True,
                          text=True, timeout=timeout, check=False, shell=False)


def _copy_safe_skill(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(f'Ya existe: {dst}; no sobrescrito')
    if not (src/'SKILL.md').is_file() or (src/'SKILL.md').is_symlink():
        raise ValueError('El repositorio descargado no contiene skills/ponytail/SKILL.md regular')
    entries: list[tuple[Path, Path]] = []
    total = 0
    for path in src.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink no permitido en skill de terceros: {path}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f'Invalid third-party skill entry: {path}')
        sz = path.stat().st_size
        total += sz
        if sz > 1_000_000 or total > 5_000_000 or len(entries) > 500:
            raise ValueError('Skill exceeds file count or size budget')
        entries.append((path, path.relative_to(src)))
    # temporary copy and atomic rename: never overwrite user-owned assets
    with tempfile.TemporaryDirectory(dir=str(dst.parent)) as temp:
        stage = Path(temp)/'prepared'
        stage.mkdir()
        for src_file, rel in entries:
            target = stage/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, target, follow_symlinks=False)
        dst.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(dst)


def install_ponytail(root: Path) -> dict[str, str]:
    dest = root/'.claude/skills/ponytail'
    if (dest/'SKILL.md').is_file():
        return {'state':'present', 'detail':'Ya existe una skill Ponytail; se conserva sin actualizar.'}
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f'Destino no apto: {dest}')
    if not shutil.which('git'):
        raise RuntimeError('Falta git para instalar Ponytail desde el repositorio oficial.')
    with tempfile.TemporaryDirectory(prefix='harness-ponytail-') as temp:
        checkout = Path(temp)/'upstream'
        result = _invoke(['git','clone','--depth','1',SOURCES['ponytail'],str(checkout)],timeout=120)
        if result.returncode:
            raise RuntimeError(f'git clone failed (exit {result.returncode}): {result.stderr[-500:]}')
        revision = _invoke(['git','-C',str(checkout),'rev-parse','HEAD'],timeout=15)
        if revision.returncode:
            raise RuntimeError('No se pudo determinar el commit upstream.')
        _copy_safe_skill(checkout/'skills/ponytail',dest)
        return {'state':'installed','commit':revision.stdout.strip(), 'location':'.claude/skills/ponytail',
                'note':'Install only the skill; never enable the full plugin, upstream hooks or unrelated files.'}


def _bin(name: str, preferred: str | None = None) -> str | None:
    # uv tool may not add user bin dir to current process PATH immediately
    if preferred and Path(preferred).is_file():
        return preferred
    located = shutil.which(name)
    if located:
        return located
    for base in (Path.home()/'.local/bin', Path.home()/'.cargo/bin'):
        candidate = base/name
        if candidate.is_file():
            return str(candidate)
    return None


def install_graphify(root: Path) -> dict[str, str]:
    dest = root/'.claude/skills/graphify'
    already_installed_skill = (dest/'SKILL.md').is_file()
    if (dest.exists() or dest.is_symlink()) and not already_installed_skill:
        raise FileExistsError(f'Destino no apto: {dest}')
    cli = _bin('graphify')
    if already_installed_skill and cli:
        return {'state':'present','detail':'Skill Graphify y CLI detectados; no se reescriben.'}
    if not cli:
        manager = _bin('uv') or _bin('pipx')
        if not manager:
            raise RuntimeError('Requiere uv o pipx para instalar el paquete oficial graphifyy (doble y).')
        result = _invoke([manager,'tool','install','graphifyy'] if Path(manager).name=='uv' else
                         [manager,'install','graphifyy'],timeout=300)
        if result.returncode:
            raise RuntimeError(f'Graphify installation failed ({result.returncode}): {result.stderr[-500:]}')
        cli = _bin('graphify')
    if not cli:
        raise RuntimeError('graphifyy instalado pero graphify no aparece en PATH ni ~/.local/bin.')
    # Register a project skill only if missing. Do not create an MCP server.
    if not already_installed_skill:
        result = _invoke([cli,'install','--project','--platform','claude'],cwd=root,timeout=90)
        if result.returncode:
            raise RuntimeError(f'Graphify installer failed ({result.returncode}): {result.stderr[-500:]}')
        if not (dest/'SKILL.md').is_file():
            raise RuntimeError('The command exited without creating .claude/skills/graphify/SKILL.md.')
    version = _invoke([cli,'--version'],timeout=15)
    return {'state':'installed','location':'.claude/skills/graphify','version':version.stdout.strip()[:120] if version.returncode==0 else 'desconocida',
            'note':'Local CLI only; index generation happens on demand, not during installation.'}


def install_ui_ux(root: Path) -> dict[str, str]:
    dest = root/'.claude/skills/ui-ux-pro-max'
    if (dest/'SKILL.md').is_file():
        return {'state':'present','detail':'Skill UI/UX ya presente; se conserva.'}
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f'Destino no apto: {dest}')
    npx = _bin('npx')
    if not npx:
        raise RuntimeError('Falta npx (Node.js/npm) para instalar ui-ux-pro-max-cli.')
    result = _invoke([npx,'--yes','ui-ux-pro-max-cli','init','--ai','claude'],cwd=root,timeout=300)
    if result.returncode:
        raise RuntimeError(f'uipro initialization failed ({result.returncode}): {result.stderr[-500:]}')
    if not (dest/'SKILL.md').is_file():
        raise RuntimeError('uipro exited without creating .claude/skills/ui-ux-pro-max/SKILL.md.')
    return {'state':'installed','location':'.claude/skills/ui-ux-pro-max',
            'note':'Upstream npm CLI; pin the production version and inspect dependency provenance.'}


INSTALLERS = {'ponytail':install_ponytail,'graphify':install_graphify,'ui-ux-pro-max':install_ui_ux}


def _profile(root: Path) -> dict[str, Any]:
    try:
        return json.loads((root/'.harness/project-profile.json').read_text(encoding='utf8'))['decisions']
    except (OSError, KeyError, ValueError) as exc:
        raise RuntimeError('Perfil no encontrado en .harness/project-profile.json') from exc


def status(root: Path, profile: dict[str,Any]) -> dict[str, Any]:
    raw: dict[str,Any] = {}
    lock = root/'.harness/external-skills-lock.json'
    if lock.is_file():
        try:
            raw = json.loads(lock.read_text(encoding='utf8'))
        except (ValueError,OSError):
            pass
    known=raw.get('skills',{}) if isinstance(raw.get('skills',{}),dict) else {}
    discovered=[p.name for p in (root/'.claude/skills').iterdir() if p.is_dir() and (p/'SKILL.md').is_file()] if (root/'.claude/skills').is_dir() and not (root/'.claude/skills').is_symlink() else []
    for name in sorted(set(enabled_names(profile)) | set(known) | set(discovered)):
        location = root/'.claude/skills'/name/'SKILL.md'
        item = raw.get('skills',{}).get(name,{}) if isinstance(raw.get('skills'),dict) else {}
        state = 'present' if location.is_file() else 'missing'
        print(f'{name}: {state}' + (f' ({item.get("state")}: {item.get("detail", "")})' if item and state=='missing' else ''))
    print('Graphify CLI:', 'disponible' if _bin('graphify') else 'no encontrado')
    _, note=write_inventory(root,profile)
    print('Inventario:',note)
    return raw


def install_all(root: Path, profile: dict[str, Any], *, permission: bool, dry_run: bool=False, selected: list[str]|None=None, record_comparison: bool=False) -> dict[str, Any]:
    if selected is not None and (not selected or any(n not in enabled_names(profile) for n in selected)):
        raise ValueError('Selection includes unknown skills or skills incompatible with this profile.')
    if not dry_run and not permission:
        raise PermissionError('Third-party installation requires explicit approval (--yes).')
    root = root.resolve()
    if (root/'.claude').is_symlink() or (root/'.claude/skills').is_symlink() or (root/'.harness').is_symlink():
        raise ValueError('Symlinked .claude/.harness paths are not allowed for external installations.')
    if not root.is_dir():
        raise RuntimeError('El destino debe existir y ser directorio.')
    if dry_run:
        for cmd in planned_commands(profile):
            print('PLAN:',cmd)
        return {'dry_run':True}
    record: dict[str,Any] = {'schema_version':1, 'sources':SOURCES, 'updated_at_utc':datetime.now(timezone.utc).isoformat(), 'skills':{}}
    old_lock = root/'.harness/external-skills-lock.json'
    if old_lock.exists():
        try:
            old = json.loads(old_lock.read_text(encoding='utf8'))
            if isinstance(old,dict) and isinstance(old.get('skills'),dict):
                record['skills'].update(old['skills'])
        except (OSError,ValueError):
            pass
    for name in (selected if selected is not None else enabled_names(profile)):
        print('Instalando/verificando:',name,flush=True)
        try:
            record['skills'][name] = INSTALLERS[name](root)
            print('  ->',record['skills'][name]['state'])
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
            record['skills'][name] = {'state':'failed','detail':str(exc)[:700]}
            print('  -> FAILED:',str(exc)[:300],file=sys.stderr)
    old_lock.parent.mkdir(parents=True,exist_ok=True)
    old_lock.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    _, note=write_inventory(root,profile)
    print('Inventario:',note)
    if record_comparison:
        from aikya.documentation.layout import record_skill_comparison
        record_skill_comparison(root,record)
    return record



def install_github_skill(root: Path, *, name: str, repo: str, skill_path: str,
                         ref: str|None, commit: str|None, permission: bool) -> dict[str, str]:
    """Importar SOLO una carpeta de Agent Skills desde un checkout aislado y aprobado."""
    if not permission:
        raise PermissionError('Installing an external skill requires explicit user approval.')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64:
        raise ValueError('Invalid skill name; use lowercase letters and hyphens.')
    if name.startswith('aikya-'):
        raise ValueError('No se puede reemplazar el espacio de comandos Aikya.')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?',repo):
        raise ValueError('Allowed source: public HTTPS GitHub repository URL (github.com/owner/repo).')
    if ref is not None and (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,120}',ref) or '..' in ref or ref.endswith('.lock')):
        raise ValueError('Invalid Git ref.')
    if commit is not None and not re.fullmatch(r'[a-fA-F0-9]{40}',commit):
        raise ValueError('El commit esperado debe tener 40 caracteres hexadecimales.')
    rel=Path(skill_path)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts or str(rel) in ('.','') or '\\' in skill_path:
        raise ValueError('Invalid skill path; use a relative path contained within the repository.')
    dest=root/'.claude/skills'/name
    if (root/'.claude').is_symlink() or (root/'.claude/skills').is_symlink() or (root/'.harness').is_symlink():
        raise ValueError('Symlinked .claude/.harness paths are not allowed for external installations.')
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f'La skill {name} ya existe; no se sobrescribe.')
    if not shutil.which('git'):
        raise RuntimeError('Git executable is unavailable.')
    with tempfile.TemporaryDirectory(prefix='aikya-skill-') as temp:
        checkout=Path(temp)/'upstream'
        args=['git','clone','--depth','1','--no-checkout']
        if ref: args+=['--branch',ref]
        args += ['--',repo,str(checkout)]
        result=_invoke(args,timeout=120)
        if result.returncode:
            raise RuntimeError(f'No fue posible descargar la fuente: {result.stderr[-250:]}')
        result=_invoke(['git','-C',str(checkout),'checkout','--force','HEAD'],timeout=60)
        if result.returncode:
            raise RuntimeError('No fue posible materializar el checkout Git.')
        rev=_invoke(['git','-C',str(checkout),'rev-parse','HEAD'],timeout=15)
        sha=rev.stdout.strip()
        if rev.returncode or not re.fullmatch(r'[a-f0-9]{40}',sha):
            raise RuntimeError('Could not verify the source commit.')
        if commit and sha.lower()!=commit.lower():
            raise ValueError('El commit descargado difiere del hash aprobado.')
        src=checkout/rel
        if not src.resolve().is_relative_to(checkout.resolve()) or src.is_symlink():
            raise ValueError('Skill path escapes the repository or is symlinked.')
        if not src.is_dir():
            raise ValueError('La ruta no contiene un directorio de skill.')
        # Validate Agent Skills contracts before copying; never execute imported code.
        md=src/'SKILL.md'
        if not md.is_file() or md.is_symlink():
            raise ValueError('Falta SKILL.md regular.')
        fm=md.read_text(encoding='utf8')[:12000]
        if not fm.startswith('---\n') or '\n---\n' not in fm:
            raise ValueError('SKILL.md carece de frontmatter Agent Skills.')
        fields=fm.split('---\n',2)[1]
        if not re.search(r'^name:\s*'+re.escape(name)+r'\s*$',fields,re.M) or not re.search(r'^description:\s*\S',fields,re.M):
            raise ValueError('SKILL.md debe declarar nombre coincidente y description.')
        dest.parent.mkdir(parents=True,exist_ok=True)
        _copy_safe_skill(src,dest)
        return {'state':'installed','source':repo,'commit':sha,'location':f'.claude/skills/{name}',
                'detail':'Skill de GitHub copiada sin ejecutar hooks ni scripts de terceros.'}


def install_custom(root: Path, profile: dict[str, Any], *, name: str, repo: str,
                   skill_path: str, ref: str|None=None, commit: str|None=None,
                   permission: bool=False, record_comparison: bool=False) -> dict[str, Any]:
    if not permission:
        raise PermissionError('Installation requires explicit approval.')
    root=root.resolve()
    if (root/'.claude').is_symlink() or (root/'.claude/skills').is_symlink() or (root/'.harness').is_symlink():
        raise ValueError('Symlinked .claude/.harness paths are not allowed for external installations.')
    lock=root/'.harness/external-skills-lock.json'
    record={'schema_version':1,'sources':SOURCES,'updated_at_utc':datetime.now(timezone.utc).isoformat(),'skills':{}}
    if lock.is_file():
        try:
            old=json.loads(lock.read_text(encoding='utf8'))
            if isinstance(old.get('skills'),dict): record['skills'].update(old['skills'])
        except (OSError,ValueError,TypeError):
            pass
    try:
        record['skills'][name]=install_github_skill(root,name=name,repo=repo,skill_path=skill_path,
                                                     ref=ref,commit=commit,permission=True)
    except (RuntimeError,OSError,ValueError) as exc:
        record['skills'][name]={'state':'failed','source':repo,'detail':str(exc)[:350]}
    lock.parent.mkdir(parents=True,exist_ok=True)
    lock.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    _, note=write_inventory(root,profile)
    print('Inventario:',note)
    if record_comparison:
        from aikya.documentation.layout import record_skill_comparison
        record_skill_comparison(root,record)
    return record

def main(argv: list[str]|None = None) -> int:
    parser = argparse.ArgumentParser(description='Aikya Harness external Agent Skills management')
    parser.add_argument('action',choices=['plan','install','status'])
    parser.add_argument('--target',type=Path,default=Path.cwd())
    parser.add_argument('--only',help='Nombres predefinidos separados por coma')
    parser.add_argument('--repo',help='URL HTTPS de repositorio de nueva skill')
    parser.add_argument('--skill-path',help='Ruta relativa al directorio que contiene SKILL.md')
    parser.add_argument('--name',help='Nombre declarado en SKILL.md')
    parser.add_argument('--ref',help='Rama o tag Git, preferiblemente inmutable')
    parser.add_argument('--commit',help='SHA-1 de 40 caracteres que se debe comprobar')
    parser.add_argument('--record-comparison',action='store_true',help='Record actual attempts only for an explicitly requested external skill installation')
    parser.add_argument('--yes',action='store_true',help='Explicitly approve running external installers')
    args=parser.parse_args(argv)
    root=args.target.expanduser().resolve()
    try:
        profile = _profile(root)
        if args.action == 'plan':
            install_all(root,profile,permission=False,dry_run=True)
            return 0
        if args.action == 'status':
            status(root,profile)
            return 0
        if any((args.repo,args.skill_path,args.name)):
            if not all((args.repo,args.skill_path,args.name)):
                raise ValueError('Una skill nueva requiere --repo, --skill-path y --name.')
            result=install_custom(root,profile,name=args.name,repo=args.repo,skill_path=args.skill_path,
                                  ref=args.ref,commit=args.commit,permission=args.yes,record_comparison=args.record_comparison)
            return 1 if result['skills'][args.name]['state']=='failed' else 0
        selected=args.only.split(',') if args.only else None
        result = install_all(root,profile,permission=args.yes,selected=selected,record_comparison=args.record_comparison)
        return 1 if any(v.get('state')=='failed' for n,v in result['skills'].items()
                        if selected is None or n in selected) else 0
    except (RuntimeError, PermissionError, ValueError, OSError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
