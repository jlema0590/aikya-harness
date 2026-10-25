#!/usr/bin/env python3
"""Create read-only snapshots to assist manual engineering/third-party reviews.

This is NOT a license compliance determination and does not fetch upstream data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from aikya.resource_paths import source_path
sys.path.insert(0,str(ROOT))
from aikya.documentation.layout import stamp


def main() -> int:
    parser = argparse.ArgumentParser(description="Aikya catalog review inventory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    components = []
    for group, glob in (
        ("agent", "engineering/agents/*.md"),
        ("skill", "engineering/skills/*/SKILL.md"),
        ("aikya-command", "aikya-skills/*/SKILL.md"),
    ):
        for path in sorted(source_path(ROOT,glob.split('/')[0]).glob('/'.join(glob.split('/')[1:]))):
            if path.is_symlink():
                raise ValueError(f"Symlinked catalog asset not reviewed: {path}")
            components.append({
                "type": group,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    snapshot = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "Aikya local curated source; no remote dependencies downloaded",
        "components": components,
    }
    (out / "catalog-inventory.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = [
        "# Aikya curated asset review",
        "",
        "This is an inventory and integrity aid, **not a legal license audit**.",
        "",
        f"- Engineering agents: {sum(x['type']=='agent' for x in components)}",
        f"- Engineering skills: {sum(x['type']=='skill' for x in components)}",
        f"- Aikya control commands: {sum(x['type']=='aikya-command' for x in components)}",
        f"- Root LICENSE found: {'yes' if (ROOT/'LICENSE').is_file() else 'NO — verify before release'}",
        f"- Third-party inventory found: {'yes' if (ROOT/'THIRD_PARTY_LICENSES.md').is_file() else 'NO — review imported assets'}",
        "",
        "## Manual review checklist",
        "",
        "- Confirm provenance and redistribution permissions for each imported agent and skill.",
        "- Retain required third-party copyright notices and applicable licenses.",
        "- Review additions, removals and SHA-256 changes against previous review artifacts.",
        "- Confirm security requirements of any external code, templates or executables.",
        "- Verify CI and GitHub publication settings before preparing a public release.",
        "",
        "No files are modified by this review, other than the report in the output directory.",
    ]
    (out / "REVIEW.md").write_text(stamp("\n".join(report)), encoding="utf-8")
    print(stamp("\n".join(report)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
