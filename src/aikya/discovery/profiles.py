#!/usr/bin/env python3
"""Project Aikya v5/v6 compatible profiles from observed, unambiguous evidence."""
from __future__ import annotations
from pathlib import Path

def build(root: Path, inventory: dict) -> dict:
    import aikya.installation.facade as install
    modules = inventory.get("modules", [])
    kind = inventory.get("project_type", "unknown")
    unresolved = []
    if inventory.get("truncated"):
        unresolved.append("Repository scan was truncated; review unexamined files.")
    if kind == "unknown":
        return {"status": "NEEDS_REVIEW", "profile": None,
                "unresolved": ["No supported manifest or infrastructure was detected."] + unresolved}
    profile = {"project_type": kind, "mode": "existing",
               "repository_layout": "singlerepo", "name": Path(root).name,
               "architecture": "existing" if kind == "development" else "undecided",
               "backend": "none", "frontend": "none", "mobile": "none",
               "package_manager": "none", "ci": "undecided",
               "deployment": "undecided", "notes": ""}
    infra = set(inventory.get("infrastructure", []))
    if kind == "development":
        roles = {"backend": [], "frontend": [], "mobile": []}
        for module in modules:
            if module.get("role") in roles:
                roles[module["role"]].append(module)
        # More than one independently deployed backend/frontend is not a single v5 role.
        for role in ("backend", "frontend", "mobile"):
            candidates = {(m["technology"], m["path"]) for m in roles[role]}
            techs = {x for x, _ in candidates}
            if len(techs) > 1 and not (role == "frontend" and techs == {"react"}):
                unresolved.append("Multiple " + role + " technologies found; choose a main component.")
                continue
            if not techs:
                continue
            tech = next(iter(techs))
            if role == "mobile":
                if tech == "flutter":
                    profile["mobile"] = "both"
                    profile["mobile_framework"] = "flutter"
                elif tech == "react-native":
                    profile["mobile"] = "both"
                    profile["mobile_framework"] = "react-native"
                else:
                    unresolved.append("Unrecognized mobile platform " + tech)
            else:
                profile[role] = tech
        root_paths = {m.get("path", ".") for m in modules}
        profile["repository_layout"] = "monorepo" if len(root_paths) > 1 else "singlerepo"
        # Cannot infer the application's framework or API style from a language alone.
        if profile["backend"] == "next" and profile["frontend"] == "none":
            profile["frontend"] = "react"
        if not any(profile[k] != "none" for k in ("backend", "frontend", "mobile")):
            unresolved.append("No unambiguous application technology for the legacy profile.")
    evidence = set(inventory.get("evidence_paths", []))
    if any(p.startswith(".github/workflows/") or "/.github/workflows/" in p for p in evidence):
        profile["ci"] = "github-actions"
    if "kubernetes" in infra:
        profile["deployment"] = "kubernetes"
    elif "docker" in infra:
        profile["deployment"] = "docker"
    profile["infrastructure"] = {
        "provider": (next((x for x in ("azure", "aws", "gcp") if x in infra), "none")),
        "iac": "terraform" if "terraform" in infra else "none",
        "configuration_management": "ansible" if "ansible" in infra else "none",
        "containers": {"enabled": "docker" in infra or "kubernetes" in infra,
                       "compose": "compose" in infra},
        "orchestration": "kubernetes" if "kubernetes" in infra else "none",
        "deployment_method": ("helm" if "helm" in infra else
                              "kustomize" if "kustomize" in infra else "yaml"
                              if "kubernetes" in infra else "none"),
        "environments": [], "image_repository": "", "container_port": None,
        "source_kind": "none",
        "helm_chart_mode": "create", "helm_chart_path": ""
    }
    if kind == "devops" and not profile["infrastructure"]["containers"]["enabled"]:
        unresolved.append("No container runtime/orchestrator found for a v5 DevOps profile.")
    if unresolved:
        return {"status": "PARTIAL", "profile": None, "unresolved": unresolved}
    try:
        normalized = install.validated(profile, Path(root))
    except (ValueError, TypeError, KeyError) as exc:
        return {"status": "PARTIAL", "profile": None,
                "unresolved": ["Legacy profile validation: " + str(exc)]}
    return {"status": "READY", "profile": normalized, "unresolved": []}
