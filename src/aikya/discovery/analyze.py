#!/usr/bin/env python3
"""Safe, interview-free onboarding of existing projects into Aikya Harness."""
from __future__ import annotations
from aikya.resource_paths import source_path
import json
import re
from pathlib import Path
from aikya.discovery.manifest import apply_assets, check_owned_tree, owned_state
from aikya.discovery.scanner import scan, safe_scope
from aikya.discovery.profiles import build
from aikya.documentation.layout import stamp

FOCUSES = ("general", "security", "architecture", "infrastructure", "operations")

def _safe(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.+/-]', "_", str(value))[:180]

def _git_revision(root: Path) -> str | None:
    head = root / ".git/HEAD"
    if head.is_symlink() or not head.is_file():
        return None
    try:
        value = head.read_text(encoding="ascii").strip()
        if re.fullmatch(r"[0-9a-f]{40,64}", value):
            return value
        if value.startswith("ref: refs/"):
            ref = value[5:]
            if re.fullmatch(r"refs/[a-zA-Z0-9_./-]+", ref) and ".." not in ref:
                path = root / ".git" / ref
                if path.is_file() and not path.is_symlink():
                    sha = path.read_text(encoding="ascii").strip()
                    return sha if re.fullmatch(r"[0-9a-f]{40,64}", sha) else None
    except (OSError, UnicodeError, ValueError):
        pass
    return None

def documents(inventory: dict, projection: dict, focus: str) -> dict[str, str]:
    modules = inventory["modules"]
    mapping = {"schema_version": 1, "status": "OBSERVED_PATHS_ONLY",
               "components": modules, "relations": [],
               "note": "No runtime or dataflow relationships inferred without evidence"}
    pending = {"unresolved": projection["unresolved"], "checks_not_run": [
        "application-build", "security-scan", "terraform-plan", "docker-build",
        "dependency-install", "remote-deploy"]}
    risks = {"security_findings": [], "verified": False,
             "note": "No scan has been run. Absence of findings is not proof of security."}
    report = ["# Aikya - existing repository analysis",
              "", "Evidence scope: observed paths only.",
              "", "Estado: " + projection["status"],
              "Tipo: " + inventory["project_type"],
              "Scope: " + _safe(inventory["scope"]),
              "Foco: " + focus,
              "Files examined: " + str(inventory["paths_examined"]),
              "Scan truncated: " + str(bool(inventory["truncated"])),
              "", "## Detected components", ""]
    report += ["- " + m["role"] + ": " + m["technology"] + " (" + _safe(m["path"]) +
               ") evidencia: " + ", ".join(_safe(p) for p in m["evidence_paths"])
               for m in modules]
    if not modules:
        report.append("- No recognized components were found")
    report += ["", "## Observed infrastructure", "",
               ", ".join(inventory["infrastructure"]) or "Not identified",
               "", "## Pending decisions", ""]
    report += ["- " + x for x in projection["unresolved"]] or ["- None needed for the profile."]
    report += ["", "## Checks not executed", "",
               "- Application build and tests: NOT EXECUTED.",
               "- Vulnerabilities and security: NOT VERIFIED.",
               "- Deployed infrastructure and remote state: NOT VERIFIED.",
               "- Scripts, containers and deployments: NOT EXECUTED.",
               "", "## Continue engineering", "",
               "Use /aikya-feature, /aikya-bugfix, /aikya-quality, /aikya-docs or /aikya-arc-review.",
               ""]
    return {
        ".aikya/analysis/inventory.json": json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/evidence.json": json.dumps({"paths": inventory["evidence_paths"],
                   "meaning": "paths observed; source contents not audited"},
                  ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/components.json": json.dumps(modules, ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/architecture-map.json": json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/pending-decisions.json": json.dumps(pending, ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/risks.json": json.dumps(risks, ensure_ascii=False, indent=2) + "\n",
        ".aikya/analysis/report.md": stamp("\n".join(report))
    }


def installation_preview(target: Path, profile: dict, inventory: dict) -> list[dict]:
    """Non-mutating, file-level preview of Aikya-owned installation paths."""
    import aikya.installation.facade as install
    import aikya.catalogs.engineering as engineering_catalog
    from aikya.documentation.bootstrap import pages
    from aikya.installation.registration import BOOTSTRAP_COMMANDS
    candidates = {
        ".aikya/answers.json", ".aikya/model-policy.json", ".aikya/code-index.json",
        "aikya/docs/memory/view/index.html", "aikya/docs/memory/view/report.md",
        ".harness/state/code-index/index.sqlite",
        ".harness/project-profile.json", ".harness/engineering-catalog.json",
        ".claude/settings.json", ".claude/rules/00-project-profile.md",
        "CLAUDE.md", "harness.json",
        "aikya/docs/tools/agents.md", "aikya/docs/skills.md"
    }
    docs_profile = dict(profile)
    docs_profile['_documentation_testing_evidence'] = [p for p in ('tests','test','src/test') if (target/p).is_dir()]
    candidates.update(pages(docs_profile, inventory["modules"]).keys())
    candidates.add('aikya/docs/indice.md')
    from aikya.installation.assets import runtime_assets
    candidates.update('aikya/scripts/harness/'+asset.destination.as_posix() for asset in runtime_assets(install.HERE,'initialized',methodology=profile.get('methodology')))
    candidates.add('aikya/scripts/harness/.bundle-manifest.json')
    if profile.get('methodology') == 'sdd':
        candidates.add('aikya/scripts/harness/sdd_engine.py')
        candidates.add('aikya/scripts/harness/sdd_templates.py')
        candidates.update('aikya/scripts/harness/sdd-templates/'+p.name for p in (source_path(install.HERE, 'sdd-templates')).glob('*.md'))
        if (target/'harness.json').is_file():
            current = install.read_json_safe(target/'harness.json')
            if not any(isinstance(c, dict) and c.get('name') == 'sdd:traceability' for c in current.get('checks', [])):
                candidates.add('.harness/backup-v611/harness.json')
    candidates.update(".claude/skills/" + n + "/SKILL.md" for n in BOOTSTRAP_COMMANDS)
    for file in install.TEMPLATE.rglob("*"):
        if not file.is_file() or file.is_symlink() or file.suffix == ".pyc":
            continue
        rel = file.relative_to(install.TEMPLATE)
        if rel.as_posix() in ("CLAUDE.md", "harness.json", ".claude/settings.json"):
            continue
        if rel.parts[0] in (".github", "infra") or rel.name in (
                ".gitignore", "Dockerfile", "docker-compose.yml", "compose.yaml") or rel.suffix in (".tf", ".tfvars"):
            continue
        target_rel = (Path("aikya/scripts") / Path(*rel.parts[1:]) if rel.parts[0] == "scripts" else
                      Path("aikya/test") / Path(*rel.parts[1:]) if rel.parts[0] == "tests" else rel)
        candidates.add(target_rel.as_posix())
    for file in (source_path(install.HERE, 'engineering')).rglob("*"):
        if file.is_file() and not file.is_symlink():
            rel = file.relative_to(source_path(install.HERE, 'engineering'))
            candidates.add((Path("aikya/scripts/harness/engineering") / rel).as_posix())
    for name in ("engineering_catalog.py", "infrastructure_profile.py",
                 "token_policy.py", "token_report.py", "model_capabilities.py",
                 "aikya_router.py", "project_discovery.py", "profile_builder.py",
                 "analysis_manifest.py", "aikya_analyze.py", "docs_layout.py", "docs_language.py", "docs_templates_en.py", "docs_templates_es.py", "docs_migration_hashes.py", "aikya_requirements.py", "documentation_templates.py", "documentation_workflows.py", "methodology.py"):
        candidates.add("aikya/scripts/harness/" + name)
    from aikya.installation.registration import EXECUTION_FILES
    candidates.update('aikya/scripts/harness/'+name for name in EXECUTION_FILES)
    for asset in (source_path(install.HERE, 'aikya-template')).rglob('*'):
        if asset.is_file() and not asset.is_symlink():
            candidates.add((Path('aikya/scripts/harness/aikya-template')/asset.relative_to(source_path(install.HERE, 'aikya-template'))).as_posix())
    selected = engineering_catalog.discover(target, profile, inventory["modules"])
    for agent in selected["agents"]:
        candidates.add(".claude/agents/" + agent + ".md")
    for skill in selected["skills"]:
        candidates.add(".claude/skills/" + skill + "/SKILL.md")
    # Never label existing user files as safe to update without their managed hashes.
    results = []
    for relative in sorted(candidates):
        path = target / relative
        action = "BLOCKED" if path.is_symlink() else "KEEP_EXISTING" if path.exists() else "CREATE_MANAGED"
        if profile.get('methodology') == 'sdd' and action == 'KEEP_EXISTING':
            if relative == 'harness.json':
                current = install.read_json_safe(path)
                gate = {'name':'sdd:traceability', 'command':['python3','aikya/scripts/harness/sdd_engine.py','lint','--root','.'], 'cwd':'.', 'required':True}
                checks = current.get('checks')
                gates = [c for c in checks if isinstance(c, dict) and c.get('name') == 'sdd:traceability'] if isinstance(checks, list) else []
                if current.get('schema_version') != 2 or not isinstance(checks, list) or (gates and gates != [gate]): action = 'BLOCKED'
                elif not gates: action = 'UPDATE_MANAGED_SDD_GATE_WITH_BACKUP'
            elif relative == '.harness/project-profile.json':
                old = install.read_json_safe(path)
                if old.get('_generated_by') != 'claude-dev-harness-interactive': action = 'BLOCKED'
                elif old.get('decisions', {}).get('methodology', 'standard') != 'sdd': action = 'UPDATE_MANAGED_METHODOLOGY'
        if relative=='.harness/project-profile.json' and action=='KEEP_EXISTING':
            old=install.read_json_safe(path)
            if old.get('_generated_by')=='claude-dev-harness-interactive' and old.get('decisions',{}).get('methodology') in (None,'standard'):
                action='UPDATE_MANAGED_METHODOLOGY_WITH_BACKUP'
                results.append({'path':'.harness/backup-odd/project-profile.json','action':'CREATE_MANAGED' if not (target/'.harness/backup-odd/project-profile.json').exists() else 'KEEP_EXISTING'})
        if relative=='.claude/settings.json' and action=='KEEP_EXISTING':
            action='MERGE_MANAGED_SETTINGS' if __import__('aikya.installation.registration',fromlist=['*']).managed_bootstrap_settings(target) else 'MERGE_VISIBILITY_PRESERVE_CUSTOM_SETTINGS'
        results.append({'path':relative,'action':action})
    from aikya.documentation.layout import migration_plan
    for op in migration_plan(target):
        if op['action']=='BLOCKED':
            results.append({'path':'aikya/docs/'+op['source'], 'action':'BLOCKED', 'reason':op['reason']})
        else:
            results.append({'path':'aikya/docs/'+op['source'], 'action':op['action'], 'target':'aikya/docs/'+op['target']})
            results.append({'path':'.harness/backup-docs-layout/'+op['source'], 'action':'CREATE_MANAGED'})
    from aikya.workflows.methodology import migration_plan as methodology_plan
    try:
        for operation in methodology_plan(target,install.read_json_safe(target/'.harness/project-profile.json'),profile.get('methodology')):
            results.append({k:v for k,v in operation.items() if k not in ('updated','expected_sha256')})
    except ValueError as exc:results.append({'path':'.harness/project-profile.json','action':'BLOCKED','reason':str(exc)})
    from aikya.installation.registration import command_retirement_plan
    try:
        for op in command_retirement_plan(target/'.claude/skills',target/'.harness'):
            results.append({'path':op['path'].relative_to(target).as_posix(),'action':op['action'],'replacement':op['replacement']})
            if op.get('backup'):results.append({'path':op['backup'].relative_to(target).as_posix(),'action':'CREATE_MANAGED'})
    except ValueError as exc:results.append({'path':'.harness/command-backups','action':'BLOCKED','reason':str(exc)})
    runtime_ops=install.documentation_runtime_plan(target)
    updates={op['path']:op for op in runtime_ops}
    results=[updates.pop(op['path'],op) for op in results]
    results.extend(updates.values())
    results.extend({'path':op['backup'],'action':'CREATE_MANAGED'} for op in runtime_ops if op.get('backup'))
    results.extend(install.managed_path_conflicts(target))
    try:
        from aikya.memory.viewer.export import preflight as memory_preflight
        memory_preflight(target)
        if (target/'.aikya/code-index.json').exists():
            from aikya.code_index.policy import load_policy
            load_policy(target)
    except ValueError:
        results.append({'path':'aikya/docs/memory/view/', 'action':'BLOCKED', 'reason':'Review custom memory policy or publication'})
    if profile.get('methodology') == 'sdd':
        try:
            from aikya.workflows.sdd.assets import prepare
            upgrades = prepare(target, install.HERE)
            by_path = {r['path']: r for r in results}
            for op in upgrades:
                by_path[op['path']] = {'path':op['path'], 'action':op['action']}
                if op['action'] == 'UPDATE_KNOWN_SDD_ASSET_WITH_BACKUP':
                    by_path[op['backup']] = {'path':op['backup'], 'action':'CREATE_MANAGED' if not (target/op['backup']).exists() else 'KEEP_EXISTING'}
            results = list(by_path.values())
        except ValueError as exc:
            results.append({'path':'SDD runtime assets', 'action':'BLOCKED', 'reason':str(exc)})
    return results


def execute(target: Path, *, scope: str = ".", focus: str = "general",
            approved: bool = False, dry_run: bool = False, report_only: bool = False,
            refresh: bool = False, docs_lang: str | None = None, methodology: str | None = None, observer=None) -> dict:
    import aikya.installation.facade as install
    target = Path(target).absolute()
    if focus not in FOCUSES:
        raise ValueError("unknown analysis focus")
    from aikya.documentation.language import resolve as resolve_docs_language
    documentation_language = resolve_docs_language(target, docs_lang)
    safe_scope(target, scope)
    check_owned_tree(target)
    inventory = scan(target, scope)
    if inventory["paths_examined"] == 0 and not inventory["evidence_paths"]:
        return {"status": "EMPTY", "recommended_command": "/aikya-init",
                "writes": False, "reason": "No project files found in scope"}
    if observer:
        observer.done('explore','Read-only project inventory collected')
        observer.event('plan','running','Resolving methodology and planned files')
    from aikya.workflows.methodology import selection
    previous = install.read_json_safe(target/'.harness/project-profile.json')
    previous_method=previous.get('decisions',{}).get('methodology') if isinstance(previous.get('decisions'),dict) else None
    if previous_method is None and previous.get('_generated_by')=='claude-dev-harness-interactive':previous_method='standard'
    chosen=selection(methodology,previous_method)
    if chosen['methodology_required']:
        return {'status':'NEEDS_METHODOLOGY','writes':False,**chosen}
    selected_method=chosen['methodology']
    projection = build(target, inventory)
    if projection['profile'] is not None:
        projection['profile']['methodology'] = selected_method
        if selected_method == 'sdd' and previous and previous.get('_generated_by') != 'claude-dev-harness-interactive':
            projection['status'] = 'NEEDS_REVIEW'
            projection['unresolved'].append('Review the custom technical profile before enabling SDD')
    docs = documents(inventory, projection, focus)
    plan = apply_assets(target, docs, refresh=refresh, dry_run=True)
    installation = installation_preview(target, projection["profile"], inventory) if projection["profile"] else []
    installation.append({"path": ".aikya/docs-policy.json", "action": "KEEP_EXISTING" if (target / ".aikya/docs-policy.json").exists() else "CREATE_MANAGED"})
    conflicts = [o for o in plan["operations"]
                 if o["action"] in ("BLOCKED", "CONFLICT_REQUIRES_REVIEW")]
    manifest_file = target / ".aikya/analysis/manifest.json"
    manifest_action = ("CONFLICT_REQUIRES_REVIEW" if manifest_file.exists() and not owned_state(target)
                       else "KEEP_EXISTING" if manifest_file.exists() else "CREATE_MANAGED")
    plan["operations"].append({"path": ".aikya/analysis/manifest.json",
                               "action": manifest_action})
    if manifest_action == "CONFLICT_REQUIRES_REVIEW":
        conflicts.append({"path": ".aikya/analysis/manifest.json",
                          "action": "CONFLICT_REQUIRES_REVIEW"})
    status = "NEEDS_REVIEW" if conflicts else projection["status"]
    if any(op["action"] == "BLOCKED" for op in installation):
        status = "NEEDS_REVIEW"
    if report_only or dry_run or not approved or status != "READY":
        return {"status": status, "writes": False, "scope": inventory["scope"],
                "focus": focus, "documentation_language": documentation_language, **chosen, "inventory": inventory,
                "unresolved": projection["unresolved"], "plan": plan["operations"] + installation,
                "conflicts": conflicts, "approval_required": status == "READY" and not approved,
                "recommended_command": "/aikya-analyze --scope <componente>" if inventory["project_type"] == "unknown"
                                       else "/aikya-analyze --approved"}
    profile = projection["profile"]
    detected = {"modules": [{"role": m["role"], "technology": m["technology"],
                            "path": m["path"]} for m in inventory["modules"]],
                "findings": inventory["evidence_paths"], "analysis_scope": inventory["scope"]}
    if observer:
        observer.done('plan','Methodology and approved Aikya file plan resolved')
        observer.event('implement','running','Installing approved Aikya-owned assets')
    actions = install.install(target, profile, detected, adopt_existing=True, docs_lang=documentation_language)
    answers = target / ".aikya/answers.json"
    if not answers.exists():
        install.safe_write(answers, json.dumps(profile, ensure_ascii=False, indent=2) + "\n", actions)
    updated = apply_assets(target, docs, refresh=refresh, dry_run=False,
                           status="READY", source_revision=_git_revision(target))
    return {"status": "READY", "writes": True, **chosen, "scope": inventory["scope"],
            "documentation_language": documentation_language, **chosen,
            "focus": focus, "actions": actions,
            "analysis_operations": updated["operations"], "unresolved": [],
            "next_commands": ["/aikya-feature", "/aikya-bugfix", "/aikya-quality",
                              "/aikya-docs", "/aikya-arc-review", "/aikya-models"]}
