#!/usr/bin/env python3
"""Offline consistency checks for Aikya's curated agents and skills.

No installation, downloads, network, code generation or repository writes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from aikya.installation import registration as aikya_setup
from aikya.catalogs import engineering as engineering_catalog


def name_from_frontmatter(path: Path) -> str:
    data = path.read_text(encoding="utf-8")
    parts = data.split("---", 2)
    if len(parts) < 3 or not data.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path.relative_to(ROOT)}")
    found = re.search(r"(?m)^name:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", parts[1])
    if not found:
        raise ValueError(f"Invalid or absent name field: {path.relative_to(ROOT)}")
    if not re.search(r"(?m)^description:\s*\S", parts[1]):
        raise ValueError(f"Missing description: {path.relative_to(ROOT)}")
    return found.group(1)


def check_catalog() -> list[str]:
    errors: list[str] = []
    agents = ROOT / 'src/aikya/resources/engineering/agents'
    skills = ROOT / 'src/aikya/resources/engineering/skills'
    if not agents.is_dir() or not skills.is_dir():
        return ["engineering/agents or engineering/skills missing"]
    agent_files = {path.stem: path for path in agents.glob("*.md")}
    skill_files = {path.parent.name: path for path in skills.glob("*/SKILL.md")}
    expected_agents = set(engineering_catalog.AGENTS)
    expected_skills = set(engineering_catalog.SKILLS)
    for title, current, expected in (
        ("agents", set(agent_files), expected_agents),
        ("skills", set(skill_files), expected_skills),
    ):
        if current != expected:
            errors.append(
                f"{title} mismatch: missing={sorted(expected-current)}, "
                f"unexpected={sorted(current-expected)}"
            )
    for label, items in (("agent", agent_files), ("skill", skill_files)):
        for name, path in sorted(items.items()):
            if path.is_symlink():
                errors.append(f"Unexpected symlink {label}: {path.relative_to(ROOT)}")
                continue
            try:
                frontmatter_name = name_from_frontmatter(path)
                if frontmatter_name != name:
                    errors.append(f"{label} name mismatch: {name} != {frontmatter_name}")
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(str(exc))
    for name, path in sorted(agent_files.items()):
        data = path.read_text(encoding="utf-8")
        frontmatter = data.split("---", 2)[1] if data.startswith("---\n") else ""
        linked = re.findall(r"(?m)^\s+-\s+([a-z0-9-]+)\s*$", frontmatter)
        for skill in linked:
            if skill not in expected_skills:
                errors.append(f"Agent {name} references unknown skill {skill}")
    if not set(engineering_catalog.BASE_AGENTS).issubset(expected_agents):
        errors.append("BASE_AGENTS references unknown agents")
    if not set(engineering_catalog.BASE_SKILLS).issubset(expected_skills):
        errors.append("BASE_SKILLS references unknown skills")
    return errors


def check_bootstrap() -> list[str]:
    errors = []
    for name in aikya_setup.BOOTSTRAP_COMMANDS:
        path = ROOT / 'src/aikya/resources/commands' / name / "SKILL.md"
        if not path.is_file() or path.is_symlink():
            errors.append(f"Missing or symlinked Aikya command: {path.relative_to(ROOT)}")
            continue
        try:
            actual = name_from_frontmatter(path)
            if actual != name:
                errors.append(f"Command name mismatch: {name} != {actual}")
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))
    from aikya.installation.assets import runtime_assets
    try:
        for asset in runtime_assets(ROOT, 'registration'):
            asset.read_bytes()
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    # Avoid silently shipping an unregistered command.
    files = {p.parent.name for p in (ROOT / 'src/aikya/resources/commands').glob("*/SKILL.md")}
    extra = files - set(aikya_setup.BOOTSTRAP_COMMANDS)
    if extra:
        errors.append(f"Unregistered Aikya commands: {sorted(extra)}")
    return errors


def main() -> int:
    failures = check_catalog() + check_bootstrap()
    if failures:
        for item in failures:
            print("ERROR:", item, file=sys.stderr)
        return 1
    print(
        "PASS: "
        f"{len(engineering_catalog.AGENTS)} engineering agents; "
        f"{len(engineering_catalog.SKILLS)} engineering skills; "
        f"{len(aikya_setup.BOOTSTRAP_COMMANDS)} Aikya commands; "
        "source files and frontmatter consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
