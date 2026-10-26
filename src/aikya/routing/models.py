#!/usr/bin/env python3
"""Offline Claude Code/Haiku capability checks. Never assumes API access."""
from __future__ import annotations
import re
import subprocess
from functools import lru_cache

MIN_HAIKU_55_CLAUDE_CODE = (2, 1, 293)
HAIKU_55_ID = "claude-haiku-5-5"

def parse_cli_version(output: str) -> tuple[int, int, int] | None:
    match = re.search(r'(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)', output)
    return tuple(map(int, match.groups())) if match else None

@lru_cache(maxsize=1)
def inspect_cli() -> dict:
    """Read-only, user-triggered version probe; does not call the Claude API."""
    try:
        run = subprocess.run(["claude", "--version"], capture_output=True,
                             text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"cli_available": False, "haiku_55_cli_compatible": False,
                "model_access_verified": False}
    version = parse_cli_version(run.stdout + "\n" + run.stderr) if run.returncode == 0 else None
    return {"cli_available": version is not None,
            "version": ".".join(map(str, version)) if version else None,
            "haiku_55_cli_compatible": bool(version and version >= MIN_HAIKU_55_CLAUDE_CODE),
            "model_access_verified": False}

def capability_status(policy: dict, cli_version: str | None = None) -> dict:
    from aikya.routing.policy import validated
    p = validated(policy)
    version = parse_cli_version(cli_version or "")
    compatible = bool(version and version >= MIN_HAIKU_55_CLAUDE_CODE)
    enabled = p["schema_version"] == 2 and p["auxiliary_enabled"] and p["user_approved"]
    confirmed = enabled and p["model_access_confirmed"]
    provider = p["model_provider"] if p["schema_version"] == 2 else "legacy"
    # Non-Anthropic providers require an explicit deployment/ARN map before use.
    ready = confirmed and compatible and provider == "anthropic"
    return {"model": HAIKU_55_ID, "provider": provider,
            "cli_compatible": compatible, "user_access_attested": confirmed,
            "ready_for_cli_delegation": ready,
            "note": "User attestation and CLI version do not prove live model availability; verify with /tasks."}
