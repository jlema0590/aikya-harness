#!/usr/bin/env python3
"""Aikya v6 model policies. v1 is compatible, v2 opts in to Haiku 5.5."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

HAIKU_45 = "claude-haiku-4-5-20251001"
HAIKU_55 = "claude-haiku-5-5"
ROLES = frozenset({"aikya-auxiliary-analyzer", "aikya-docs-assistant", "log-summarizer"})
AUX_TASKS = frozenset({"extraction", "classification", "routing", "documentation", "log-summary"})
MODEL_NAMES = frozenset({"inherit", "opus", "sonnet", "haiku", HAIKU_45, HAIKU_55})
V1_DEFAULT = {"schema_version": 1, "planning_model": "opus",
              "orchestration_model": "opus", "routine_model": "inherit",
              "auxiliary_model": "inherit", "auxiliary_enabled": False,
              "user_approved": False}
DEFAULT = {**V1_DEFAULT, "schema_version": 2, "auxiliary_model": HAIKU_55,
           "model_provider": "anthropic", "model_access_confirmed": False,
           "allowed_tasks": sorted(AUX_TASKS), "routing_mode": "hybrid",
           "confidence_threshold": 0.85, "max_delegation_depth": 1,
           "require_read_only": True, "fallback_model": "inherit"}

def validated(raw: dict | None) -> dict:
    """Return a safe, normalized policy without changing the input or v1 semantics."""
    if raw is None:
        return dict(DEFAULT)
    if not isinstance(raw, dict):
        raise ValueError("model policy must be a JSON object")
    version = raw.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError("unsupported model policy schema")
    defaults = V1_DEFAULT if version == 1 else DEFAULT
    unknown = set(raw) - set(defaults)
    if unknown:
        raise ValueError("unknown model policy fields: " + ", ".join(sorted(unknown)))
    result = {**defaults, **raw}
    for key in ("planning_model", "orchestration_model", "routine_model", "auxiliary_model"):
        if not isinstance(result[key], str) or result[key] not in MODEL_NAMES:
            raise ValueError("unsupported model selection: " + key)
    if result["routine_model"] == HAIKU_45:
        raise ValueError("Haiku 4.5 is restricted to approved auxiliary tasks")
    for key in ("auxiliary_enabled", "user_approved"):
        if type(result[key]) is not bool:
            raise ValueError(key + " must be boolean")
    if result["auxiliary_enabled"] and not result["user_approved"]:
        raise ValueError("auxiliary delegation requires explicit user approval")
    if version == 1:
        # Existing approved 4.5 policies keep their exact model; no automatic upgrade.
        return result
    if result["auxiliary_model"] == HAIKU_45:
        raise ValueError("v2 uses Haiku 5.5; keep legacy Haiku 4.5 in v1 until migration is approved")
    if result["auxiliary_model"] == "haiku":
        raise ValueError("v2 must use an explicit Haiku 5.5 ID, not a provider-dependent alias")
    if result["fallback_model"] != "inherit":
        raise ValueError("only explicit fallback to the existing user model is supported")
    if result["model_provider"] not in ("anthropic", "bedrock", "google", "foundry", "aws-platform", "unknown"):
        raise ValueError("unknown model provider")
    if type(result["model_access_confirmed"]) is not bool:
        raise ValueError("model_access_confirmed must be boolean")
    if type(result["require_read_only"]) is not bool or not result["require_read_only"]:
        raise ValueError("auxiliary agents must remain read only")
    if (type(result["max_delegation_depth"]) is not int or
            result["max_delegation_depth"] != 1):
        raise ValueError("auxiliary delegation depth must equal one")
    if result["routing_mode"] not in ("hybrid", "deterministic"):
        raise ValueError("unknown routing mode")
    threshold = result["confidence_threshold"]
    if type(threshold) not in (int, float) or not 0.5 <= threshold <= 1.0:
        raise ValueError("confidence_threshold must be between 0.5 and 1")
    tasks = result["allowed_tasks"]
    if (not isinstance(tasks, list) or
            any(not isinstance(task, str) or task not in AUX_TASKS for task in tasks) or
            len(set(tasks)) != len(tasks)):
        raise ValueError("allowed_tasks must contain unique permitted auxiliary tasks")
    # Provider access is not implied by knowing a published model ID.
    return result

def auxiliary_ready(policy: dict, task: str | None = None) -> bool:
    p = validated(policy)
    if not p["auxiliary_enabled"] or not p["user_approved"]:
        return False
    if p["schema_version"] == 1:
        return task is None or task in AUX_TASKS
    if p["routing_mode"] == "deterministic" or not p["model_access_confirmed"]:
        return False
    if p["model_provider"] != "anthropic":
        # A provider-specific deployment/profile must first be explicitly configured.
        return False
    return task is None or task in p["allowed_tasks"]

def resolved_agent_model(role: str, policy: dict) -> str:
    p = validated(policy)
    if role == "planner":
        return p["planning_model"]
    if role == "orchestrator":
        return p["orchestration_model"]
    if role in ROLES:
        if p["schema_version"] == 1:
            # Preserve existing v1 routing for log-summarizer, but do not enable new agents.
            if role == "log-summarizer" and auxiliary_ready(p):
                return p["auxiliary_model"]
            return p["routine_model"]
        tasks = ({"extraction", "classification", "routing"} if role == "aikya-auxiliary-analyzer"
                 else {"documentation"} if role == "aikya-docs-assistant" else {"log-summary"})
        if any(auxiliary_ready(p, task) for task in tasks):
            return p["auxiliary_model"]
    return p["routine_model"]

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Aikya model policy (offline)")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--role", default="developer")
    args = parser.parse_args()
    policy = validated(json.loads(args.policy.read_text(encoding="utf8")) if args.policy else None)
    print(json.dumps({"policy": policy, "role": args.role,
                      "resolved_routing": resolved_agent_model(args.role, policy)},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
