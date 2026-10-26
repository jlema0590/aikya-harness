"""Focused installer preflight responsibilities."""
from __future__ import annotations
import json
from aikya.discovery.layout import validate_layout
from aikya.discovery.infrastructure import validated as validate_infrastructure
from aikya.installation.defaults import HERE
from aikya.installation.context import InstallationPlan
from aikya.installation.discovery import read_json_safe
from aikya.installation.migrations import documentation_runtime_plan,managed_path_conflicts


def prepare_installation(target,profile,detected,adopt_existing,docs_lang,context):
    from aikya.memory.viewer.export import preflight as memory_preflight
    from aikya.core.checkpoints import safe_file
    safe_file(target,'.gitignore')
    memory_policy=None
    if (target/'.aikya/code-index.json').exists():
        from aikya.code_index.policy import load_policy
        memory_policy=load_policy(target)
    if memory_policy is None or memory_policy.auto_export:
        memory_preflight(target)
    HERE=context.source_root
    TEMPLATE=context.template_root
    if adopt_existing and profile.get('mode') != 'existing':
        raise ValueError('adopt_existing requires a legacy-compatible existing profile')
    from aikya.documentation.language import resolve as resolve_docs_language
    documentation_language = resolve_docs_language(target, docs_lang)
    validate_layout(profile)
    # Older installed harnesses may invoke this function without validated().
    from aikya.workflows.methodology import normalize_methodology
    profile = {**profile, 'methodology':normalize_methodology(profile.get('methodology')), 'project_type':profile.get('project_type','development'), 'infrastructure': validate_infrastructure(profile)}
    path_conflicts=managed_path_conflicts(target)
    if path_conflicts:raise ValueError('Managed path review required: '+json.dumps(path_conflicts))
    from aikya.documentation.layout import migration_plan, migrate
    doc_operations = migration_plan(target)
    if any(op['action'] == 'BLOCKED' for op in doc_operations):
        raise ValueError('Documentation layout migration requires review: '+json.dumps(doc_operations))
    from aikya.documentation.composition import validate_bootstrap_sources
    validate_bootstrap_sources()
    runtime_operations=documentation_runtime_plan(target, context=context)
    if any(op['action']=='BLOCKED' for op in runtime_operations):
        raise ValueError('Runtime migration requires review: '+json.dumps(runtime_operations))
    from aikya.installation.runtime import prepare_bundle,apply_bundle
    from aikya.installation.registration import command_retirement_plan
    command_retirement_plan(target/'.claude/skills',target/'.harness')
    if profile['methodology'] not in ('odd', 'sdd'):
        raise ValueError('Invalid engineering methodology')
    previous_profile = read_json_safe(target/'.harness/project-profile.json')
    previous_decisions = previous_profile.get('decisions', {})
    if isinstance(previous_decisions, dict) and previous_decisions.get('methodology') == 'sdd':
        profile['methodology'] = 'sdd'  # Disabling SDD requires a separately reviewed migration.
    if profile['methodology'] == 'sdd' and previous_profile and previous_profile.get('_generated_by') != 'claude-dev-harness-interactive':
        raise ValueError('Review the custom technical profile before enabling SDD')
    bundle=prepare_bundle(target/'aikya/scripts/harness',HERE,'initialized',methodology=profile['methodology'])
    from aikya.documentation.claude import render as render_claude
    claude_contract=render_claude(profile,detected['modules']) if not (target/'CLAUDE.md').exists() else None
    sdd_operations = []
    if profile['methodology'] == 'sdd':
        from aikya.workflows.sdd.assets import prepare as prepare_sdd_assets
        from aikya.workflows.sdd.engine import rel_file
        rel_file(target, 'harness.json')
        sdd_operations = prepare_sdd_assets(target, HERE)
    if profile['methodology'] == 'sdd' and (target/'harness.json').exists():
        manifest = target/'harness.json'
        if manifest.is_symlink(): raise ValueError('Symlinked quality manifest is not supported')
        current = read_json_safe(manifest)
        gate = {'name':'sdd:traceability', 'command':['python3','aikya/scripts/harness/sdd_engine.py','lint','--root','.'], 'cwd':'.', 'required':True}
        existing = current.get('checks')
        if current.get('schema_version') != 2 or not isinstance(existing, list):
            raise ValueError('Review the custom quality manifest before enabling SDD')
        gates = [c for c in existing if isinstance(c, dict) and c.get('name') == 'sdd:traceability']
        if gates and gates != [gate]: raise ValueError('Customized SDD gate requires review')
        for part in (target/'.harness/backup-v611', target/'.harness/backup-v611/harness.json'):
            if part.is_symlink(): raise ValueError('Symlinked SDD backup is not supported')
    backup=target/'.harness/backup-odd/project-profile.json'
    if previous_profile.get('_generated_by')=='claude-dev-harness-interactive' and previous_decisions.get('methodology') in (None,'standard'):
        if any(p.is_symlink() for p in (backup,*backup.parents) if p==target or target in p.parents):raise ValueError('Unsafe methodology backup')
    from aikya.workflows.methodology import migration_plan as methodology_plan,apply_migration as apply_methodology
    methodology_operations=methodology_plan(target,previous_profile,profile['methodology'])
    return InstallationPlan(context=context,target=target,profile=profile,detected=detected,adopt_existing=adopt_existing,documentation_language=documentation_language,previous_profile=previous_profile,previous_decisions=previous_decisions,doc_operations=doc_operations,sdd_operations=sdd_operations,methodology_operations=methodology_operations,claude_contract=claude_contract,bundle=bundle)
