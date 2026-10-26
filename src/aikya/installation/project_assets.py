"""Focused installer project assets responsibilities."""
from __future__ import annotations
from aikya.resource_paths import source_path
import hashlib
import shutil
from pathlib import Path
from aikya.documentation.layout import asset_bytes,stamp
from aikya.installation.defaults import HERE,TEMPLATE,V3_TEMPLATE_HASHES
from aikya.installation.context import InstallationPlan
from aikya.installation.io import safe_write,upgrade_exact_markdown_source
from aikya.installation.migrations import migrate_v55_project_config


def copy_project_template(plan:InstallationPlan,actions:list[str])->None:
    context=plan.context
    HERE=context.source_root
    TEMPLATE=context.template_root
    target=plan.target
    adopt_existing=plan.adopt_existing
    for source in sorted(TEMPLATE.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts or source.suffix == '.pyc':
            continue
        rel = source.relative_to(TEMPLATE)
        if rel.parent == Path('scripts/harness') and rel.stem in {'scaffold','infrastructure','run_checks','skills_lint','docs_guard'}:
            continue
        if rel.as_posix() in ('CLAUDE.md','harness.json','.claude/settings.json') or (adopt_existing and (rel.parts[0] in ('.github', 'infra') or rel.name in ('.gitignore', 'Dockerfile', 'compose.yml', 'compose.yaml', 'docker-compose.yml', 'docker-compose.yaml') or rel.suffix in ('.tf', '.tfvars'))):
            continue
        dest = target / (Path('aikya/scripts') / Path(*rel.parts[1:]) if rel.parts[0]=='scripts' else Path('aikya/test') / Path(*rel.parts[1:]) if rel.parts[0]=='tests' else rel)
        rendered=asset_bytes(dest,source.read_bytes())
        if dest.exists():
            if upgrade_exact_markdown_source(target,source,dest,actions):continue
            old_hash = V3_TEMPLATE_HASHES.get(rel.as_posix())
            if old_hash and dest.is_file() and not dest.is_symlink() and hashlib.sha256(dest.read_bytes()).hexdigest() == old_hash:
                backup = target/'.harness/backup-v3'/rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                if not backup.exists():
                    shutil.copy2(dest, backup)
                dest.write_bytes(rendered)
                shutil.copymode(source,dest)
                actions.append('UPDATED FROM v3 (backup created) '+str(dest))
            else:
                actions.append('PRESERVED (sin sobrescribir) '+str(dest))
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(rendered)
            shutil.copymode(source,dest)
            actions.append('CREADO '+str(dest))
    if not adopt_existing:
        migrate_v55_project_config(target,actions, context=context)


def install_commands(plan:InstallationPlan,actions:list[str])->None:
    context=plan.context
    HERE=context.source_root
    TEMPLATE=context.template_root
    target=plan.target
    # v6: retain legacy commands with lightweight aliases.
    from aikya.installation.registration import BOOTSTRAP_COMMANDS
    for original in sorted((TEMPLATE/'.claude/skills').glob('*/SKILL.md')):
        old_name = original.parent.name
        if old_name == 'project-bootstrap' or old_name.startswith('aikya-'):
            continue
        alias = 'aikya-' + old_name
        # Public wrappers are registered below. Never shadow them with copied skills.
        if alias in BOOTSTRAP_COMMANDS or alias in __import__('aikya.installation.registration',fromlist=['*']).LEGACY_RENAMES:
            continue
        destination = target/'.claude/skills'/alias/'SKILL.md'
        body = ('---\nname: '+alias+'\ndescription: Alias de compatibilidad para /'+old_name+
                '.\ndisable-model-invocation: true\n---\n'
                '<!-- AIKYA BOOTSTRAP MANAGED -->\n'
                '# /'+alias+'\nConsulta la skill de proyecto /'+old_name+
                ' y aplica el procedimiento original con los mismos permisos.\n')
        if destination.is_file() and not destination.is_symlink():
            legacy = original.read_text(encoding='utf8').replace(
                'name: '+old_name+'\n','name: '+alias+'\n',1)
            if destination.read_text(encoding='utf8') == legacy:
                destination.write_text(stamp(body),encoding='utf8')
                actions.append('MIGRADO alias gestionado '+str(destination))
                continue
        safe_write(destination,body,actions)
    # Registrar todos los comandos gestionados Aikya cuando el proyecto se inicializa.
    # Los wrappers tienen la marca AIKYA BOOTSTRAP MANAGED y no sustituyen skills personalizadas.
    from aikya.installation.registration import BOOTSTRAP_COMMANDS
    for name in BOOTSTRAP_COMMANDS:
        src=source_path(HERE, 'aikya-skills')/name/'SKILL.md'
        dst=target/'.claude/skills'/name/'SKILL.md'
        if not src.is_file():
            continue
        if dst.exists() and not dst.is_symlink() and __import__('aikya.installation.registration',fromlist=['*']).verified_skill_upgrade(dst,src):
            rendered=asset_bytes(dst,src.read_bytes())
            if dst.read_bytes()!=rendered:
                dst.write_bytes(rendered)
                actions.append('UPDATED managed skill '+str(dst))
        elif not dst.exists():
            safe_write(dst,src.read_text(encoding='utf8'),actions)
    # Migrate old wrappers only when they match the exact original managed asset.
    from aikya.installation.registration import retire_legacy_commands
    retire_legacy_commands(target/'.claude/skills',target/'.harness',actions)
    for _scope in (target/'.aikya/runtime', HERE):
        if (_scope/'bootstrap_skills').is_dir():
            retire_legacy_commands(target/'.claude/skills',_scope,actions)
            break
    # v4 also generated an unmarked alias from an internal skill.
    old_alias=target/'.claude/skills/aikya-project-bootstrap/SKILL.md'
    original=TEMPLATE/'.claude/skills/project-bootstrap/SKILL.md'
    if old_alias.is_file() and not old_alias.is_symlink() and original.is_file():
        expected=original.read_text(encoding='utf8').replace('name: project-bootstrap\n',
                                                               'name: aikya-project-bootstrap\n',1)
        if old_alias.read_text(encoding='utf8')==expected:
            old_alias.unlink()
            try: old_alias.parent.rmdir()
            except OSError: pass
            actions.append('RETIRADO alias anterior aikya-project-bootstrap')
    # Comandos no Aikya heredados permanecen disponibles en el proyecto.
    # Disponible también cuando Aikya se instaló desde la fuente sin bootstrap.


def activate_engineering(plan:InstallationPlan,actions:list[str])->None:
    from aikya.catalogs.engineering import discover,install_selected
    selected=discover(plan.target,plan.profile,plan.detected['modules'])
    actions.extend(install_selected(plan.target,selected,source=source_path(plan.context.source_root,'engineering')))
