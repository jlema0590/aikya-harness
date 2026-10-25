#!/usr/bin/env python3
"""Offline smoke tests of Aikya examples without writing into the repository.

Validates example decisions, specialist selection and planned artifacts only.
Does not install tools, run an application generator or deploy infrastructure.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aikya.installation import requirements as aikya_requirements
from aikya.documentation import bootstrap as doc_bootstrap
from aikya.catalogs import engineering as engineering_catalog
from aikya.installation import facade as install


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Module not readable: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, '_module', module)


from aikya.tools import scaffold as SCAFFOLD
from aikya.tools import infrastructure as INFRA


def verify_one(path: Path) -> tuple[str, int, int]:
    answers = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(answers, dict):
        raise ValueError("answers.json must contain a JSON object")
    with tempfile.TemporaryDirectory(prefix="aikya-smoke-") as tmp:
        root = Path(tmp)
        profile = install.validated(answers, root)
        kind = profile.get("project_type", "development")
        chosen = engineering_catalog.discover(root, profile, [])
        if not set(chosen["agents"]).issubset(engineering_catalog.AGENTS):
            raise ValueError("Selected agents not in curated catalog")
        if not set(chosen["skills"]).issubset(engineering_catalog.SKILLS):
            raise ValueError("Selected skills not in curated catalog")
        commands, manual = SCAFFOLD.command_plans(profile)
        planned, pending = INFRA.specs(root, profile)
        if any(not isinstance(item, str) for item in pending):
            raise ValueError("Infrastructure pending decisions must be strings")
        if kind in ("infrastructure", "devops"):
            if commands:
                raise ValueError("Autonomous mode requested application generators")
            forbidden = ("apps/", "packages/", "contracts/")
            if any(filename.startswith(forbidden) for filename in planned):
                raise ValueError("Autonomous mode planned application workspaces")
            folders = doc_bootstrap.infra_files(profile)
            if any(filename.startswith(forbidden) for filename in folders):
                raise ValueError("Autonomous mode requested application folders")
            app_tools = {"node", "java", "javac", "dotnet", "flutter", "adb", "xcodebuild"}
            toolset = set(aikya_requirements.required_tools(profile))
            if toolset & app_tools:
                raise ValueError(f"Autonomous mode unexpectedly requires {sorted(toolset & app_tools)}")
        # The temporary project must still be empty. No apply/generate/install.
        if list(root.iterdir()):
            raise ValueError("A planning operation wrote to disk")
        return kind, len(commands), len(planned)


def main() -> int:
    files = sorted((ROOT / "examples").glob("*/answers.json"))
    if not files:
        print("ERROR: no examples/*/answers.json", file=sys.stderr)
        return 1
    failures = []
    for file in files:
        try:
            mode, commands, files_count = verify_one(file)
            print(f"PASS {file.parent.name}: {mode}, {commands} app plans, {files_count} infra files")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            failures.append((file.parent.name, str(exc)))
    for label, issue in failures:
        print(f"FAIL {label}: {issue}", file=sys.stderr)
    print(f"Verified {len(files)-len(failures)}/{len(files)} example profiles")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
