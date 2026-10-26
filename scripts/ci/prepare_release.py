#!/usr/bin/env python3
"""Prepare a reviewable VERSION/CHANGELOG change without publishing."""
from __future__ import annotations
import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from release_contract import parse_version, ReleaseError, read_version
from aikya.documentation.layout import stamp

TAG=re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")


def prepare(root:Path, name:str, date:str|None=None) -> tuple[str,str]:
    if not TAG.fullmatch(name):
        raise ReleaseError("Version must use vX.Y.Z without suffixes")
    next_version=name[1:]
    current,parsed=read_version(root)
    if parse_version(next_version)<=parsed:
        raise ReleaseError(f"New version {name} must be higher than v{current}")
    changelog=root/"CHANGELOG.md"
    if not changelog.is_file() or changelog.is_symlink():
        raise ReleaseError("CHANGELOG.md is missing")
    content=changelog.read_text(encoding="utf-8")
    if re.search(r"(?m)^##\s+"+re.escape(name)+r"(?=\s|$)",content):
        raise ReleaseError("Version already exists in CHANGELOG.md")
    heading=re.search(r"(?m)^## (?:Unreleased|Sin publicar)\s*$",content)
    if heading is None:
        raise ReleaseError("Add a ## Unreleased heading with reviewed notes before versioning")
    rest=content[heading.end():]
    nxt=re.search(r"(?m)^## ",rest)
    notes=rest[:nxt.start()] if nxt else rest
    if not re.search(r"(?m)^\s*[-*]\s+\S",notes):
        raise ReleaseError("No changes listed under ## Unreleased")
    today=date or datetime.now(timezone.utc).date().isoformat()
    replacement=f"## Unreleased\n\n## {name} — {today}"
    revised=content[:heading.start()]+replacement+content[heading.end():]
    from release_contract import notes_from_changelog
    notes_from_changelog(revised,next_version)
    changelog.write_text(stamp(revised),encoding="utf-8")
    (root/"VERSION").write_text(next_version+"\n",encoding="utf-8")
    return name,today


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="Prepare a version PR; never publish")
    parser.add_argument("--version",required=True)
    args=parser.parse_args(argv)
    try:
        version,date=prepare(ROOT,args.version)
    except (OSError,ReleaseError,UnicodeError) as exc:
        print("ERROR PREPARE:",exc,file=sys.stderr)
        return 2
    print(f"Prepared {version} — {date} in CHANGELOG.md and VERSION; review before merge.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
