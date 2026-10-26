#!/usr/bin/env python3
"""Conservative ownership and idempotent writes for Aikya analysis-only assets."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

MARKER = "aikya-analyze"
MANIFEST = ".aikya/analysis/manifest.json"

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def owned_state(root: Path) -> dict:
    path = root / MANIFEST
    if path.is_symlink() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf8"))
        return data if data.get("_generated_by") == MARKER and isinstance(data.get("managed_paths"), dict) else {}
    except (OSError, ValueError, UnicodeError, AttributeError):
        return {}

def validate_destination(root: Path, relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts or not relative.startswith(".aikya/analysis/"):
        raise ValueError("analysis assets must stay within .aikya/analysis/")
    node = root
    for fragment in p.parts:
        node = node / fragment
        if node.is_symlink():
            raise ValueError("symlinked analysis destinations are prohibited")
    return node

def assess(root: Path, relative: str, content: str, previous: dict,
           *, refresh: bool = False) -> str:
    path = validate_destination(root, relative)
    encoded = content.encode("utf8")
    if not path.exists():
        return "CREATE_MANAGED"
    if not path.is_file():
        return "BLOCKED"
    try:
        current = path.read_bytes()
    except OSError:
        return "BLOCKED"
    if current == encoded:
        return "KEEP_EXISTING"
    old_hash = previous.get("managed_paths", {}).get(relative)
    if old_hash and old_hash == digest(current):
        return "UPDATE_MANAGED" if refresh else "CONFLICT_REQUIRES_REVIEW"
    return "CONFLICT_REQUIRES_REVIEW"

def apply_assets(root: Path, contents: dict[str, str], *, refresh: bool = False,
                 dry_run: bool = True, status: str = "READY",
                 source_revision: str | None = None) -> dict:
    root = root.absolute()
    from aikya.documentation.layout import stamp
    contents={name:stamp(body) if Path(name).suffix.lower()=='.md' else body for name,body in contents.items()}
    previous = owned_state(root)
    operations = []
    owned = dict(previous.get("managed_paths", {}))
    for relative, content in sorted(contents.items()):
        if relative == MANIFEST:
            raise ValueError("manifest file is managed internally")
        operation = assess(root, relative, content, previous, refresh=refresh)
        operations.append({"path": relative, "action": operation})
        if not dry_run and operation in ("CREATE_MANAGED", "UPDATE_MANAGED"):
            path = validate_destination(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf8")
            owned[relative] = digest(content.encode("utf8"))
        elif not dry_run and operation == "KEEP_EXISTING":
            owned[relative] = digest(content.encode("utf8"))
    if not dry_run:
        manifest = {
            "_generated_by": MARKER, "schema_version": 1,
            "analysis_version": "6.0.0",
            "created_at": previous.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "scope": json.loads(contents[".aikya/analysis/inventory.json"]).get("scope", "."),
            "scanner_versions": {"project_discovery": 1, "profile_builder": 1},
            "source_revision": source_revision,
            "status": status,
            "managed_paths": dict(sorted(owned.items())),
            "redaction_rules": ["no-secrets", "no-source-copy", "paths-only"],
        }
        manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        path = validate_destination(root, MANIFEST)
        if path.exists() and not previous:
            operations.append({"path": MANIFEST, "action": "CONFLICT_REQUIRES_REVIEW"})
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_text(encoding="utf8") != manifest_text:
                path.write_text(manifest_text, encoding="utf8")
                operations.append({"path": MANIFEST, "action": "UPDATE_MANAGED" if previous else "CREATE_MANAGED"})
            else:
                operations.append({"path": MANIFEST, "action": "KEEP_EXISTING"})
    return {"operations": operations, "managed_paths": owned}

def check_owned_tree(root: Path) -> None:
    """Reject symlinks in paths shared with installer; avoid out-of-tree writes."""
    for top in (".aikya", ".harness", ".claude", "aikya"):
        current = root / top
        if current.is_symlink():
            raise ValueError("symlinked harness path: " + top)
        if not current.is_dir():
            continue
        for base, dirs, files in __import__("os").walk(current, followlinks=False):
            for name in dirs + files:
                if (Path(base) / name).is_symlink():
                    raise ValueError("symlink found within harness-owned directory")
    for name in ("CLAUDE.md", "harness.json", ".gitignore"):
        if (root / name).is_symlink():
            raise ValueError("symlinked project configuration: " + name)
