#!/usr/bin/env python3
"""Validate Claude Code Agent Skills and subagents without third-party dependencies."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from aikya.resource_paths import source_path
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_MODELS = {"inherit", "opus", "sonnet", "haiku"}
ALLOWED_PERMISSIONS = {"default", "plan", "acceptEdits", "dontAsk"}
KNOWN_TOOLS = {"Read", "Grep", "Glob", "Edit", "Write", "Bash", "LSP",
               "Agent", "Skill", "WebFetch", "WebSearch", "NotebookEdit"}
READ_ONLY_AGENTS = {"architect", "cloud-architect", "code-reviewer",
                    "qa-reviewer", "security-reviewer", "documentation-maintainer",
                    "planner", "aikya-auxiliary-analyzer", "aikya-docs-assistant",
                    "log-summarizer"}


def parse_frontmatter(path: Path) -> tuple[dict, list[str]]:
    issues = []
    try:
        text = path.read_text(encoding="utf8")
    except (OSError, UnicodeError):
        return {}, ["Cannot read " + str(path)]
    if not text.startswith("---\n"):
        return {}, ["Missing leading frontmatter: " + str(path)]
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, ["Unterminated YAML frontmatter: " + str(path)]
    lines = text[4:end].splitlines()
    fields: dict[str, object] = {}
    current = None
    for lineno, line in enumerate(lines, start=2):
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):(?:\s+(.*))?$", line)
        if match:
            key, raw = match.group(1), (match.group(2) or "").strip()
            if key in fields:
                issues.append(f"{path}:{lineno}: duplicate frontmatter key {key}")
            if raw in (">", ">-", "|", "|-"):
                fields[key] = ""
            else:
                fields[key] = raw.strip("'\"") if raw else []
            current = key
        elif line.startswith("  - ") or line.startswith("- "):
            if current is None or not isinstance(fields.get(current), list):
                issues.append(f"{path}:{lineno}: unexpected YAML list")
            else:
                fields[current].append(line.strip()[2:].strip())
        elif line.startswith((" ", "\t")) and current is not None:
            if isinstance(fields.get(current), str):
                fields[current] = (str(fields[current]) + " " + line.strip()).strip()
            else:
                issues.append(f"{path}:{lineno}: unexpected scalar continuation")
        elif line.strip():
            issues.append(f"{path}:{lineno}: unsupported YAML syntax")
    if not text[end + 5:].strip():
        issues.append(str(path) + ": missing instructions")
    return fields, issues


def _names(value: object) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def inspect_skill(path: Path) -> list[str]:
    fields, issues = parse_frontmatter(path)
    if not fields:
        return issues
    name = fields.get("name")
    desc = fields.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name) or name != path.parent.name or len(name) > 64:
        issues.append(f"{path}: invalid or mismatched skill name")
    if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
        issues.append(f"{path}: missing or invalid skill description")
    if "disable-model-invocation" in fields and fields["disable-model-invocation"] not in ("true", "false"):
        issues.append(f"{path}: invalid disable-model-invocation boolean")
    if len(path.read_text(encoding="utf8").splitlines()) > 500:
        issues.append(f"{path}: move lengthy instructions into referenced files")
    return issues


def inspect_agent(path: Path, skill_names: set[str]) -> list[str]:
    fields, issues = parse_frontmatter(path)
    if not fields:
        return issues
    name = fields.get("name")
    desc = fields.get("description")
    if not isinstance(name, str) or name != path.stem or not NAME_RE.fullmatch(name):
        issues.append(f"{path}: invalid or mismatched agent name")
    if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
        issues.append(f"{path}: missing or invalid agent description")
    if fields.get("model", "inherit") not in ALLOWED_MODELS:
        issues.append(f"{path}: unsupported model alias")
    if fields.get("permissionMode", "default") not in ALLOWED_PERMISSIONS:
        issues.append(f"{path}: permission mode needs review")
    turns = fields.get("maxTurns")
    if turns is not None and (not str(turns).isdigit() or not 1 <= int(turns) <= 100):
        issues.append(f"{path}: invalid maxTurns")
    tools = _names(fields.get("tools", []))
    if not tools:
        issues.append(f"{path}: declare allowed tools explicitly")
    issues += [f"{path}: unknown tool {t}" for t in tools if t not in KNOWN_TOOLS]
    if name in READ_ONLY_AGENTS and {"Edit", "Write", "Bash", "NotebookEdit"} & set(tools):
        issues.append(f"{path}: read-only reviewer exposes mutating/command tools")
    for skill in _names(fields.get("skills", [])):
        if skill not in skill_names:
            issues.append(f"{path}: missing referenced skill {skill}")
    return issues


def validate(root: Path = ROOT) -> list[str]:
    sets = (
        (source_path(root,"aikya-skills")).glob("*/SKILL.md"),
        (source_path(root,"engineering/skills")).glob("*/SKILL.md"),
        (source_path(root,"template/.claude/skills")).glob("*/SKILL.md"),
    )
    skills = [path for files in sets for path in files]
    agents = list((source_path(root,"engineering/agents")).glob("*.md")) + list(
        (source_path(root,"template/.claude/agents")).glob("*.md"))
    known = {path.parent.name for path in skills}
    issues = []
    for path in skills:
        issues.extend(inspect_skill(path))
    for path in agents:
        issues.extend(inspect_agent(path, known))
    if not skills or not agents:
        issues.append("No skills or agents found")
    return issues


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    print("Source Agent Skills and Claude Code subagent metadata: VALID")
