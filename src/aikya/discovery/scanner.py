#!/usr/bin/env python3
"""Bounded, read-only detection for existing repositories; never executes project code."""
from __future__ import annotations
import json
import re
from pathlib import Path

IGNORED = {".git", ".aikya", ".harness", ".claude", "aikya", "node_modules",
           ".venv", "venv", "dist", "build", "target", ".next", ".nuxt", ".angular",
           "__pycache__", ".terraform", ".gradle", "vendor", "coverage", ".output"}
EVIDENCE = {"package.json", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock",
            "uv.lock", "pom.xml", "build.gradle", "build.gradle.kts", "gradle.properties",
            "pubspec.yaml", "angular.json", "Dockerfile", "docker-compose.yml",
            "docker-compose.yaml", "compose.yml", "compose.yaml", "Chart.yaml",
            "kustomization.yaml", "terraform.tf", "main.tf", "providers.tf", "backend.tf",
            "terragrunt.hcl", "ansible.cfg", "requirements.yml", "global.json"}
SUFFIXES = {".csproj", ".sln", ".tf", ".tfvars", ".yml", ".yaml", ".sh", ".ps1"}
LANGUAGES = {"java", "node", "python", "dotnet", "vue", "angular", "react",
             "next", "flutter", "kotlin", "ios"}
MAX_FILES = 12000
MAX_BYTES = 100_000

def safe_scope(root: Path, scope: str = ".") -> Path:
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError("project root must be an existing non-symlink directory")
    raw = Path(scope)
    if raw.is_absolute() or any(p in ("..", "") for p in raw.parts):
        raise ValueError("scope must be an existing relative project path")
    path = root
    for part in raw.parts:
        if part == ".":
            continue
        path = path / part
        if path.is_symlink():
            raise ValueError("symlinked scopes are not supported")
    if not path.is_dir() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("scope must resolve to a directory inside the project")
    return path

def _manifest(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
        return {}
    try:
        val = json.loads(path.read_text(encoding="utf8"))
        return val if isinstance(val, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}

def scan(root: Path, scope: str = ".") -> dict:
    """Inventory paths and manifest declarations only; never stores source contents."""
    root = Path(root).absolute()
    focus = safe_scope(root, scope)
    modules = []
    infra = set()
    evidence = []
    seen = set()
    files = 0
    truncated = False
    # sorted traversal provides deterministic order; no symlinks or vendor trees.
    stack = [(focus, 0)]
    while stack:
        folder, depth = stack.pop()
        try:
            entries = sorted(folder.iterdir(), key=lambda x: x.name)
        except OSError:
            continue
        dirs = []
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if depth < 6 and entry.name not in IGNORED and not entry.name.startswith("."):
                    dirs.append(entry)
                # .github workflows are recognized separately at root
                continue
            if not entry.is_file() or entry.name in ('CLAUDE.md', 'harness.json'):
                continue  # Managed onboarding metadata must not affect source inventory.
            files += 1
            if files > MAX_FILES:
                truncated = True
                break
            rel = entry.relative_to(root).as_posix()
            if entry.name not in EVIDENCE and entry.suffix not in SUFFIXES:
                continue
            if entry.stat().st_size > MAX_BYTES:
                continue
            evidence.append(rel)
            def add(role, tech):
                identity = (role, tech, folder.relative_to(root).as_posix())
                if identity not in seen:
                    seen.add(identity)
                    modules.append({"role": role, "technology": tech, "path": identity[2],
                                    "evidence_paths": [rel], "confidence": "detected"})
            if entry.name == "package.json":
                data = _manifest(entry)
                dep = data.get("dependencies", {})
                dev = data.get("devDependencies", {})
                deps = {**(dep if isinstance(dep, dict) else {}),
                        **(dev if isinstance(dev, dict) else {})}
                if "@angular/core" in deps:
                    add("frontend", "angular")
                if "vue" in deps or "nuxt" in deps:
                    add("frontend", "vue")
                if "next" in deps:
                    add("backend", "next")
                    add("frontend", "react")
                elif "react" in deps:
                    add("frontend", "react")
                if any(x in deps for x in ("express", "fastify", "@nestjs/core", "hono", "koa")):
                    add("backend", "node")
                if "react-native" in deps or "expo" in deps:
                    add("mobile", "react-native")
            elif entry.name in ("pyproject.toml", "requirements.txt", "Pipfile"):
                add("backend", "python")
            elif entry.name in ("pom.xml", "build.gradle", "build.gradle.kts"):
                add("backend", "java")
            elif entry.suffix == ".csproj":
                add("backend", "dotnet")
            elif entry.name == "pubspec.yaml":
                add("mobile", "flutter")
            elif entry.name == "angular.json":
                add("frontend", "angular")
            elif entry.name == "Dockerfile" or entry.name.startswith("compose") or entry.name.startswith("docker-compose"):
                infra.add("docker")
                if "compose" in entry.name:
                    infra.add("compose")
            elif entry.suffix in (".tf", ".tfvars") or entry.name in ("terragrunt.hcl", "terraform.tf"):
                infra.add("terraform")
                # Inspect limited declarative provider blocks; never read tfvars/secrets.
                if entry.suffix == ".tf":
                    try:
                        with entry.open(encoding="utf8") as handle:
                            excerpt = handle.read(12000)
                        if re.search(r'\b(?:provider\s*["\']azurerm["\']|azurerm_\w+)', excerpt):
                            infra.add("azure")
                        elif re.search(r'\b(?:provider\s*["\']aws["\']|aws_\w+)', excerpt):
                            infra.add("aws")
                        elif re.search(r'\b(?:provider\s*["\']google["\']|google_\w+)', excerpt):
                            infra.add("gcp")
                    except (OSError, UnicodeError):
                        pass
            elif entry.name in ("Chart.yaml", "kustomization.yaml"):
                infra.add("kubernetes")
                if entry.name == "Chart.yaml":
                    infra.add("helm")
                else:
                    infra.add("kustomize")
            elif entry.name in ("ansible.cfg", "requirements.yml"):
                infra.add("ansible")
            elif entry.suffix in (".sh", ".ps1"):
                infra.add("scripts")
        if files > MAX_FILES:
            break
        for child in reversed(dirs):
            stack.append((child, depth + 1))
    # Do not read arbitrary workflow contents.
    for pipeline in (".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile"):
        location = focus / pipeline
        if location.is_dir() and not location.is_symlink():
            infra.add("ci")
            evidence.extend(p.relative_to(root).as_posix() for p in sorted(location.glob("*.yml"))[:40]
                            if p.is_file() and not p.is_symlink())
        elif location.is_file() and not location.is_symlink():
            infra.add("ci")
            evidence.append(location.relative_to(root).as_posix())
    roots = {m["path"] for m in modules}
    app = bool(modules)
    kind = ("development" if app else "infrastructure" if "terraform" in infra or "ansible" in infra
            else "devops" if infra & {"docker", "compose", "kubernetes", "ci"} else "unknown")
    return {"schema_version": 1, "scope": focus.relative_to(root).as_posix(),
            "project_type": kind, "modules": sorted(modules, key=lambda m: (m["path"], m["role"], m["technology"])),
            "infrastructure": sorted(infra), "evidence_paths": sorted(set(evidence)),
            "paths_examined": files, "truncated": truncated,
            "status": "DETECTED" if kind != "unknown" else "NEEDS_REVIEW"}
