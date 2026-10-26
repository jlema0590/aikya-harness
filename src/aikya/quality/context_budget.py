#!/usr/bin/env python3
"""Conservative static approximation of Aikya's always-visible context metadata."""
from __future__ import annotations
from aikya.resource_paths import source_root,source_path
import argparse
import json
from pathlib import Path

def estimate(root: Path, chars_per_token: float = 3.5) -> dict:
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be positive")
    files = []
    claude = root / "CLAUDE.md"
    if claude.is_file():
        files.append(claude)
    rules = root / ".claude/rules"
    if rules.is_dir():
        files += sorted(rules.glob("*.md"))
    total_chars = sum(len(p.read_text(encoding="utf8")) for p in files)
    metadata_chars = 0
    for folder, suffix in (("skills", "SKILL.md"), ("agents", "*.md")):
        base = root / ".claude" / folder
        if not base.is_dir():
            continue
        items = sorted(base.rglob(suffix))
        for item in items:
            source = item.read_text(encoding="utf8")
            if not source.startswith("---\n"):
                continue
            fields = source.split("---", 2)[1]
            for line in fields.splitlines():
                if line.startswith(("name:", "description:")):
                    metadata_chars += len(line) + 1
    estimate_tokens = round((total_chars + metadata_chars) / chars_per_token)
    return {"root": str(root), "proxy_tokens": estimate_tokens,
            "instruction_chars": total_chars, "metadata_chars": metadata_chars,
            "chars_per_token": chars_per_token,
            "disclaimer": "Static proxy, not Claude tokenizer, system prompt, or billable usage."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=source_path(source_root(),"template"))
    parser.add_argument("--max-proxy-tokens", type=int, default=None)
    args = parser.parse_args()
    report = estimate(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.max_proxy_tokens is not None and report["proxy_tokens"] > args.max_proxy_tokens:
        print("Context proxy exceeded configured ceiling")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
