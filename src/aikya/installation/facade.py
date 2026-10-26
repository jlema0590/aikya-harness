"""Compatible installer API and command line; implementations are grouped by responsibility."""
from __future__ import annotations
from aikya.resource_paths import source_root, source_path, project_root
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from aikya.documentation.bootstrap import pages as doc_pages, infra_files, _infra_files as infra_source_files
from aikya.documentation.layout import asset_bytes, stamp, generated
from aikya.catalogs.external import enabled_names, planned_commands, install_all
from aikya.discovery.layout import LAYOUTS, app_count, layout_of, validate_layout
from aikya.discovery.infrastructure import validated as validate_infrastructure, selected as selected_infrastructure
from aikya.installation.defaults import *
from aikya.installation.context import InstallerContext
from aikya.installation.discovery import root_directories,relative,read_json_safe,detect_project
from aikya.installation.interview import choice,ask,yesno,specialized_interview,interview
from aikya.installation.profile import validated
from aikya.installation.checks import package_command,manager_for,make_checks
from aikya.installation.io import upgrade_exact_markdown_source,safe_write
from aikya.installation.documents import md_text,context_markdown,project_bootstrap_en,project_bootstrap
from aikya.installation.migrations import copy_legacy_docs,managed_path_conflicts
from aikya.installation.migrations import documentation_runtime_plan as _documentation_runtime_plan


def documentation_runtime_plan(target: Path) -> list[dict]:
    return _documentation_runtime_plan(target,context=InstallerContext(HERE,TEMPLATE))
from aikya.installation.pipeline import install as _install


def install(target: Path, profile: dict[str, Any], detected: dict[str, Any], dry_run: bool=False, *, adopt_existing: bool=False, docs_lang: str | None = None) -> list[str]:
    return _install(target,profile,detected,dry_run,adopt_existing=adopt_existing,docs_lang=docs_lang,context=InstallerContext(HERE,TEMPLATE))
from aikya.installation.io import merge_settings as _merge_settings


def merge_settings(target: Path, actions: list[str]) -> None:
    return _merge_settings(target,actions,context=InstallerContext(HERE,TEMPLATE))
from aikya.installation.migrations import migrate_v55_project_config as _migrate_v55_project_config


def migrate_v55_project_config(target: Path, actions: list[str]) -> None:
    return _migrate_v55_project_config(target,actions,context=InstallerContext(HERE,TEMPLATE))
from aikya.installation.migrations import upgrade_documentation_runtime as _upgrade_documentation_runtime


def upgrade_documentation_runtime(target: Path, actions: list[str]) -> None:
    return _upgrade_documentation_runtime(target,actions,context=InstallerContext(HERE,TEMPLATE))


def only_aikya_bootstrap(target:Path) -> bool:
    """Allow new mode only if the directory contains bootstrap assets or answers.

    Global Aikya stores its runtime in HOME and writes only `.aikya/answers.json`
    to a new target; project-scope Aikya also has a managed local runtime.
    An unrelated code file or settings file will *always* reject new mode.
    """
    state=target/'.aikya'
    answers=state/'answers.json'
    marker=state/'bootstrap.json'
    local_bootstrap=(marker.is_file() and not marker.is_symlink() and
                     read_json_safe(marker).get('_generated_by')=='aikya-setup')
    answers_only=answers.is_file() and not answers.is_symlink() and bool(read_json_safe(answers))
    if not (local_bootstrap or answers_only):
        return False
    allowed_roots={'.git','.aikya'} | ({'.claude'} if local_bootstrap else set())
    if any(entry.name not in allowed_roots or entry.is_symlink() for entry in target.iterdir()):
        return False
    claude=target/'.claude'
    if claude.is_dir():
        from aikya.installation.registration import BOOTSTRAP_COMMANDS
        safe={f'skills/{name}/SKILL.md' for name in BOOTSTRAP_COMMANDS}
        settings=claude/'settings.json'
        if settings.is_file() and not settings.is_symlink():
            raw=read_json_safe(settings)
            hooks=raw.get('hooks',{}).get('SessionStart',[]) if isinstance(raw.get('hooks',{}),dict) else []
            registered=any('aikya_session.py' in str(h.get('command',''))
                           for group in hooks if isinstance(group,dict)
                           for h in group.get('hooks',[]) if isinstance(h,dict))
            if registered:
                safe.add('settings.json')
        if any(entry.relative_to(claude).as_posix() not in safe for entry in claude.rglob('*') if entry.is_file()):
            return False
    permitted={'runtime','bootstrap.json','answers.json'} if local_bootstrap else {'answers.json'}
    if any(entry.name not in permitted or entry.is_symlink() for entry in state.iterdir()):
        return False
    return True



def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description='Technical interview and safe Claude Code installer')
    parser.add_argument('--target',type=Path,default=Path.cwd(),help='Repositorio existente o nuevo directorio')
    parser.add_argument('--methodology',choices=['odd','sdd','standard'],default=None,help='Choose ODD or SDD; standard is a legacy alias')
    parser.add_argument('--answers',type=Path,help='JSON answers for non-interactive installation')
    parser.add_argument('--dry-run',action='store_true',help='Mostrar plan sin escribir archivos')
    parser.add_argument('--allow-bootstrap',action='store_true',help='Allow new mode only with verified Aikya-only bootstrap')
    parser.add_argument('--display-name',default=None,help='Nombre local que se muestra en el saludo de Claude Code (no se versiona)')
    parser.add_argument('--docs-lang',choices=['en','es'],default=None,help='Language of Aikya living documentation only')
    parser.add_argument('--external',choices=['ask','install','plan','skip'],default=None,help='Third-party skills: request consent, install only with approval, preview or skip')
    args=parser.parse_args(argv)
    target=args.target.expanduser().resolve()
    if target.exists() and not target.is_dir():
        parser.error('--target debe ser un directorio')
    detected=detect_project(target) if target.exists() else {'modules':[],'findings':['Directorio nuevo.']}
    if not args.answers and target.exists() and any(target.iterdir()) and not (args.allow_bootstrap and only_aikya_bootstrap(target)):
        print('ERROR: interactive init is only for new projects; use /aikya-analyze for existing repositories.',file=sys.stderr)
        return 2
    try:
        if args.answers:
            answers=read_json_safe(args.answers)
            if not answers:
                raise ValueError('--answers is empty, invalid or unreadable.')
            profile=validated({**answers,**({'methodology':args.methodology} if args.methodology else {})},target)
            welcome_name = args.display_name if args.display_name is not None else answers.get('welcome_name', '')
        else:
            profile=validated(interview(target,detected),target)
            if args.docs_lang is None and not args.dry_run:
                from aikya.documentation.language import read as read_docs_language
                if read_docs_language(target) is None:
                    args.docs_lang=choice('Select the language of Aikya living documentation', ['en','es'], 'en')
            welcome_name = args.display_name if args.display_name is not None else ask(
                'Name displayed in Claude Code welcome (blank = git user.name)', '')
    except (ValueError,KeyboardInterrupt,EOFError) as exc:
        print(f'Interview canceled or invalid: {exc}',file=sys.stderr)
        return 2
    if profile['mode']=='existing' and not target.exists():
        print('ERROR: mode=existing requiere una carpeta de proyecto existente.',file=sys.stderr)
        return 2
    if profile['mode']=='new' and target.exists() and any(target.iterdir()) and not (args.allow_bootstrap and only_aikya_bootstrap(target)):
        if args.answers:
            print('ERROR: mode=new requires an empty directory (overwrite protection).',file=sys.stderr)
            return 2
        print('El directorio de destino ya contiene archivos.')
        if not yesno('Continue without overwriting existing files?',False):
            return 2
    print('\n=== RESUMEN DE DECISIONES ===')
    print(json.dumps(profile,indent=2,ensure_ascii=False))
    if not args.answers and not args.dry_run and not yesno('Install the harness with this profile?',True):
        print('Installation canceled. No files were created.')
        return 0
    try:
        actions=install(target,profile,detected,dry_run=args.dry_run,docs_lang=args.docs_lang)
    except (OSError,UnicodeError,ValueError) as exc:
        print(f'ERROR during installation: {exc}',file=sys.stderr)
        return 1
    if not args.dry_run and welcome_name:
        if not isinstance(welcome_name, str) or not welcome_name.strip():
            print('NOTICE: invalid welcome name; not saved.', file=sys.stderr)
        else:
            # La identidad es por usuario/equipo local, no forma parte del perfil compartido.
            welcome_file = target / '.harness/welcome.json'
            if welcome_file.is_symlink():
                print('NOTICE: welcome.json is a symlink; not modified.', file=sys.stderr)
            else:
                welcome_file.parent.mkdir(parents=True, exist_ok=True)
                welcome_file.write_text(json.dumps({'display_name': welcome_name.strip()[:48]},
                    ensure_ascii=False, indent=2) + '\n', encoding='utf8')
                actions.append('IDENTIDAD LOCAL configurada en .harness/welcome.json (ignorado por Git)')
    print('\n=== RESULTADO ===')
    for a in actions:
        print('-',a)
    failed_external = False
    if not args.dry_run:
        policy = args.external or ('plan' if args.answers else 'ask')
        if policy in ('ask','install','plan'):
            print('\n=== AGENT SKILLS EXTERNAS ===')
            for command in planned_commands(profile):
                print('PLAN:', command)
        if policy == 'ask':
            policy = 'install' if yesno('Approve downloading and running official third-party installers?',False) else 'plan'
        if policy == 'install':
            print('\nInstalando skills externas seleccionadas ...')
            record = install_all(target, profile, permission=True)
            failed = [k for k,v in record.get('skills',{}).items() if v.get('state')=='failed']
            if failed:
                failed_external = True
                print('AVISO: instalaciones externas pendientes: '+', '.join(failed),file=sys.stderr)
                print('Use /aikya-install-skill from Claude Code with explicit approval.')
        elif policy == 'plan':
            print('Skills externas PENDIENTES; para instalarlas tras revisar procedencia:')
            print('Desde Claude Code utiliza /aikya-install-skill, con autorización explícita.')
        print('\nSiguiente: desde Claude Code ejecuta /aikya-doctor y /aikya-scaffold plan; luego /aikya-quality.')
    return 3 if failed_external else 0



if __name__=='__main__':
    sys.exit(main())
