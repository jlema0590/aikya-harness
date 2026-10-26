"""Focused installer configuration responsibilities."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import shutil
from aikya.discovery.infrastructure import selected as selected_infrastructure
from aikya.installation.context import InstallationPlan
from aikya.installation.checks import make_checks
from aikya.installation.discovery import read_json_safe
from aikya.installation.documents import context_markdown
from aikya.installation.io import merge_settings,safe_write
from aikya.installation.migrations import upgrade_documentation_runtime


def apply_profile(plan:InstallationPlan,actions:list[str])->None:
    context=plan.context
    HERE=context.source_root
    TEMPLATE=context.template_root
    target=plan.target
    profile=plan.profile
    detected=plan.detected
    adopt_existing=plan.adopt_existing
    documentation_language=plan.documentation_language
    doc_operations=plan.doc_operations
    sdd_operations=plan.sdd_operations
    methodology_operations=plan.methodology_operations
    bundle=plan.bundle
    from aikya.workflows.methodology import apply_migration as apply_methodology
    from aikya.documentation.layout import migrate
    from aikya.installation.runtime import apply_bundle
    target.mkdir(parents=True, exist_ok=True)
    if methodology_operations:
        apply_methodology(target,methodology_operations)
        actions.extend('UPDATED methodology with backup: '+op['path'] for op in methodology_operations)
    if doc_operations:
        migrate(target, approved=True)
        actions.append('MIGRATED managed documentation layout with backups')
    if sdd_operations:
        from aikya.workflows.sdd.assets import apply as apply_sdd_assets
        apply_sdd_assets(target,sdd_operations,actions)
    from aikya.documentation.language import write_approved as save_docs_language
    if save_docs_language(target, documentation_language):
        actions.append('CREATED .aikya/docs-policy.json')
    upgrade_documentation_runtime(target, actions, context=context)
    apply_bundle(target/'aikya/scripts/harness',bundle,actions)
    # Save a structured profile; update only installer-owned profiles on repeated runs.
    profile_path = target / '.harness/project-profile.json'
    payload = {'_generated_by':'claude-dev-harness-interactive', 'schema_version':1,
               'decisions':profile, 'detected':detected}
    if profile_path.exists():
        old = read_json_safe(profile_path)
        if old.get('_generated_by')=='claude-dev-harness-interactive' and old.get('decisions',{}).get('methodology') in (None,'standard'):
            backup=target/'.harness/backup-odd/project-profile.json'
            if backup.is_symlink() or backup.parent.is_symlink():raise ValueError('Unsafe methodology backup')
            backup.parent.mkdir(parents=True,exist_ok=True)
            if not backup.exists():shutil.copy2(profile_path,backup)
        if adopt_existing and old.get('_generated_by') == 'claude-dev-harness-interactive' and old.get('decisions', {}).get('methodology', 'standard') != profile['methodology']:
            old['decisions']['methodology'] = profile['methodology']
            profile_path.write_text(json.dumps(old, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
            actions.append('UPDATED explicitly selected methodology in managed profile')
        elif adopt_existing or old.get('_generated_by') != 'claude-dev-harness-interactive':
            actions.append('PRESERVED non-Aikya profile: '+str(profile_path))
        else:
            profile_path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
            actions.append('ACTUALIZADO '+str(profile_path))
    else:
        safe_write(profile_path, json.dumps(payload,indent=2,ensure_ascii=False)+'\n',actions)


def configure_project(plan:InstallationPlan,actions:list[str])->None:
    context=plan.context
    HERE=context.source_root
    TEMPLATE=context.template_root
    target=plan.target
    profile=plan.profile
    detected=plan.detected
    adopt_existing=plan.adopt_existing
    claude_contract=plan.claude_contract
    model_policy = target/'.aikya/model-policy.json'
    if not model_policy.exists():
        from aikya.routing.policy import DEFAULT
        safe_write(model_policy, json.dumps(DEFAULT,ensure_ascii=False,indent=2)+'\n', actions)

    if not adopt_existing or not (target/'.claude/settings.json').exists() or __import__('aikya.installation.registration',fromlist=['*']).managed_bootstrap_settings(target):
        merge_settings(target, actions, context=context)
    else:
        actions.append('PRESERVED existing settings.json during adoption')
    from aikya.middleware.configuration import register_visibility
    from aikya.installation.hook_commands import render_managed_hook, status_command, host_shell
    python = Path(sys.executable).absolute()
    observer = render_managed_hook(python, target / 'aikya/scripts/harness/execution_observer.py', ('hook',), host_shell())
    bar = status_command(python, target / 'aikya/scripts/harness/aikya_statusline.py')
    register_visibility(target/'.claude/settings.json',observer,bar,actions,target/'.aikya/visibility-proposed.json')
    claude = target / 'CLAUDE.md'
    if not claude.exists():
        safe_write(claude,claude_contract,actions)
    else:
        actions.append('PRESERVED existing CLAUDE.md; profile is available at .claude/rules/00-project-profile.md')
    safe_write(target/'.claude/rules/00-project-profile.md', context_markdown(profile,detected['modules']), actions, replace_managed=True)
    checks = [{'name':'docs:structure', 'command':['python3','aikya/scripts/harness/docs_guard.py','base'], 'cwd':'.', 'required':True}, {'name':'skills:format', 'command':['python3','aikya/scripts/harness/skills_lint.py'], 'cwd':'.', 'required':True}] + make_checks(target,profile,detected['modules'])
    if selected_infrastructure(profile['infrastructure']):
        checks.append({'name':'infra:static',
                       'command':['python3','aikya/scripts/harness/infrastructure.py','validate'],
                       'cwd':'.','required':False})
    if profile['methodology'] == 'sdd':
        checks.append({'name':'sdd:traceability', 'command':['python3','aikya/scripts/harness/sdd_engine.py','lint','--root','.'], 'cwd':'.', 'required':True})
    safe_write(target/'harness.json',json.dumps({'schema_version':2,'checks':checks},indent=2,ensure_ascii=False)+'\n',actions)
    if profile['methodology'] == 'sdd':
        manifest = target/'harness.json'
        if manifest.is_symlink(): raise ValueError('Symlinked quality manifest is not supported')
        current = read_json_safe(manifest)
        if current.get('schema_version') != 2 or not isinstance(current.get('checks'), list):
            raise ValueError('Review the custom quality manifest before enabling SDD')
        gate = checks[-1]
        existing_gates = [c for c in current['checks'] if isinstance(c, dict) and c.get('name') == 'sdd:traceability']
        if existing_gates and existing_gates != [gate]:
            raise ValueError('Customized SDD gate requires review; no checks were replaced')
        if not existing_gates:
            backup = target/'.harness/backup-v611/harness.json'
            if backup.is_symlink() or backup.parent.is_symlink(): raise ValueError('Symlinked SDD backup is not supported')
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists(): shutil.copy2(manifest, backup)
            current['checks'].append(gate)
            manifest.write_text(json.dumps(current, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
            actions.append('ADDED SDD traceability check; original quality manifest backed up')
