#!/usr/bin/env python3
"""Deterministic, safe Aikya routing. Optional semantic output is advisory only.

This module never calls a model, executes commands, reads source files or changes
a user's Claude Code model. Claude Code subagents implement approved delegation.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from aikya.routing.policy import validated, auxiliary_ready, resolved_agent_model, AUX_TASKS

CATEGORIES = frozenset({"general", "bug", "feature", "documentation", "devops",
                        "infrastructure", "architecture", "security", "testing"})
KNOWN_ROLES = frozenset({"java-developer", "flutter-developer", "terraform-engineer",
                         "cicd-engineer", "kubernetes-engineer", "docker-developer",
                         "node-backend-developer", "python-developer", "test-engineer",
                         "documentation-maintainer", "developer", "vue-developer", "angular-developer"})
RISK = re.compile(r'\b(terraform\s+(?:apply|destroy)|destroy|destruir|production|producci[oó]n|'
                  r'secret(?:s|os)?|credential(?:s)?|credenciales|auth(?:entication|orization)?|'
                  r'autenticaci[oó]n|autorizaci[oó]n|migraci[oó]n(?:\s+de\s+datos)?|'
                  r'deploy|desplegar|privilegios|iam)\b', re.I)
ACTION = re.compile(r'\b(crear|crea|implementa|añade|agrega|corrige|corregir|'
                    r'fix|desarrolla|configura|genera|construye|refactoriza)\b', re.I)

def classify(request: str) -> str:
    p = request.lower()
    if re.search(r'\b(terraform|opentofu|bicep|ansible|infraestructura|landing zone)\b', p):
        return "infrastructure"
    if re.search(r'\b(devops|pipeline|ci/cd|helm|kubernetes|github actions)\b', p):
        return "devops"
    if re.search(r'\b(seguridad|vulnerabilidad|cve|security)\b', p):
        return "security"
    if re.search(r'\b(arquitectura|refactorizaci[oó]n|architecture)\b', p):
        return "architecture"
    if re.search(r'\b(corrige|corregir|bug|fallo|repara|fix)\b', p) and ACTION.search(p):
        return "bug"
    # A feature with tests/documentation is still a feature, not a test-only task.
    if re.search(r'\b(api|endpoint|flutter|java|react|feature|funcionalidad)\b', p) and ACTION.search(p):
        return "feature"
    if re.search(r'\b(documenta|documentaci[oó]n|runbook|readme)\b', p) and ACTION.search(p):
        return "documentation"
    if re.search(r'\b(test(?:s|ing)?|pruebas)\b', p) and ACTION.search(p):
        return "testing"
    return "general"

def _specialist(category: str, request: str) -> str:
    p = request.lower()
    if category == "testing":
        return "test-engineer"
    if category == "documentation":
        return "documentation-maintainer"
    if category == "infrastructure":
        return "terraform-engineer" if "terraform" in p else "developer"
    if "angular" in p:
        return "angular-developer"
    if "vue" in p or "nuxt" in p:
        return "vue-developer"
    if category == "devops":
        return "cicd-engineer"
    for needle, role in (("flutter", "flutter-developer"), ("java", "java-developer"),
                         ("spring", "java-developer"), ("python", "python-developer"),
                         ("node", "node-backend-developer")):
        if needle in p:
            return role
    return "developer"

def semantic_advice(raw: dict, threshold: float) -> dict | None:
    """Validate untrusted Haiku JSON; never accept tools, permissions or model changes."""
    if not isinstance(raw, dict) or any(k not in {"category", "confidence", "suggested_role",
                                                  "requires_planning"} for k in raw):
        return None
    confidence = raw.get("confidence")
    category = raw.get("category")
    role = raw.get("suggested_role")
    if (type(confidence) not in (int, float) or not threshold <= confidence <= 1 or
            category not in CATEGORIES or
            (role is not None and role not in KNOWN_ROLES) or
            type(raw.get("requires_planning", False)) is not bool):
        return None
    return {"category": category, "suggested_role": role,
            "requires_planning": raw.get("requires_planning", False)}

def route(request: str, policy: dict | None = None, *,
          affected_components: int = 1, semantic: dict | None = None,
          analysis_only: bool = False, odd_facts: dict | None = None) -> dict:
    if not isinstance(request, str) or len(request) > 10000:
        raise ValueError("request must be text of at most 10000 characters")
    if type(affected_components) is not int or affected_components < 1:
        raise ValueError("affected_components must be positive")
    from aikya.workflows.odd import classify_work
    continuity=classify_work({'read_only':True} if analysis_only else odd_facts or {})
    p = validated(policy)
    category = classify(request)
    dangerous = bool(RISK.search(request)) and bool(ACTION.search(request) or
                re.search(r'\b(terraform\s+(?:apply|destroy)|deploy|desplegar)\b', request, re.I))
    approved_aux = False
    if p["schema_version"] == 2 and auxiliary_ready(p):
        from aikya.routing.models import capability_status, inspect_cli
        approved_aux = capability_status(p, inspect_cli().get("version"))["ready_for_cli_delegation"]
    advice = None
    known_category = category
    if semantic is not None and approved_aux and auxiliary_ready(p, "routing"):
        advice = semantic_advice(semantic, p["confidence_threshold"])
    if advice and category == "general" and not dangerous:
        category = advice["category"]
    specialist = _specialist(category, request)
    # Never let an untrusted semantic model override a deterministic specialist.
    if advice and known_category == "general" and not dangerous and advice["suggested_role"]:
        specialist = advice["suggested_role"]
    complex_work = (affected_components >= 3 or category == "architecture" or
                    bool(advice and advice["requires_planning"]))
    if category in ("devops", "infrastructure") and affected_components >= 3:
        coordinator = "orchestrator"
    elif complex_work:
        coordinator = "planner"
    else:
        coordinator = None
    # A semantic suggestion may increase complexity, never bypass risk approval.
    uncertain = category == "general" and not advice
    aux_task = "classification" if uncertain else None
    use_auxiliary = bool(aux_task and approved_aux and auxiliary_ready(p, aux_task))
    if category == "documentation" and not dangerous and approved_aux and auxiliary_ready(p, "documentation"):
        use_auxiliary = True
        aux_task = "documentation"
    if dangerous:
        use_auxiliary = False
        aux_task = None
    selected = coordinator or specialist
    inferred_roles = [specialist]
    if "docker" in request.lower() and specialist != "docker-developer":
        inferred_roles.append("docker-developer")
    skills = ["security-audit"] if category == "security" else []
    if analysis_only:
        return {"odd_continuity":continuity,"mode": "analysis_only", "read_only": True,
                "category": category, "recommended_role": selected,
                "recommended_roles": inferred_roles, "recommended_skills": skills,
                "recommended_model": resolved_agent_model(selected, p),
                "requires_approval": False, "writes": False,
                "note": "Read-only routing advice; no LLM invoked and no permissions granted."}
    return {"odd_continuity":continuity,"category": category, "recommended_role": selected,
            "recommended_model": resolved_agent_model(selected, p),
            "specialist": specialist, "auxiliary_task": aux_task if use_auxiliary else None,
            "auxiliary_agent": ("aikya-docs-assistant" if aux_task == "documentation"
                                else "aikya-auxiliary-analyzer") if use_auxiliary else None,
            "requires_approval": dangerous or bool(coordinator),
            "risk_flag": dangerous, "semantic_advice_accepted": bool(advice),
            "note": "Routing advice only; no LLM invoked, no changes executed."}

def main():
    parser = argparse.ArgumentParser(description="Safe, offline Aikya routing preview")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--request", required=True)
    parser.add_argument("--components", type=int, default=1)
    parser.add_argument("--analysis-only", action="store_true")
    parser.add_argument("--odd-facts",type=Path,help="Reviewed boolean work facts; advisory only")
    args = parser.parse_args()
    p = json.loads(args.policy.read_text(encoding="utf8")) if args.policy else None
    print(json.dumps(route(args.request, p, affected_components=args.components,
                           analysis_only=args.analysis_only,odd_facts=json.loads(args.odd_facts.read_text()) if args.odd_facts else None),
                     indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
