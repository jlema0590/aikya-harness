#!/usr/bin/env python3
"""Read-only, local Claude Code session usage report. No prompts are persisted."""
from __future__ import annotations
import argparse
import json
from collections import defaultdict
from pathlib import Path

from aikya.middleware.usage import KEYS,estimate_haiku_55_request,summarize

def estimate_cost(report: dict, price_catalog: dict) -> dict:
    """Opt-in USD estimates from explicitly provided per-million-token rates."""
    if not isinstance(price_catalog, dict) or not isinstance(price_catalog.get("models"), dict):
        raise ValueError("price catalog must contain a models mapping")
    rates = {"input_tokens": "input", "output_tokens": "output",
             "cache_creation_input_tokens": "cache_creation",
             "cache_read_input_tokens": "cache_read"}
    values = {}
    missing = []
    for model, usage in report["models"].items():
        price = price_catalog["models"].get(model)
        if not isinstance(price, dict) or any(
            not isinstance(price.get(k), (int, float)) or price[k] < 0 for k in rates.values()
        ):
            missing.append(model)
            continue
        values[model] = round(sum(usage.get(key, 0) * price[label] / 1_000_000
                                  for key, label in rates.items()), 8)
    return {"currency": "USD", "by_model_estimated": values,
            "total_estimated": round(sum(values.values()), 8) if not missing else None,
            "models_missing_prices": missing,
            "note": "Not a provider bill; assumes supplied rates and transcript usage are comparable."}


def main():
    p = argparse.ArgumentParser(description="Aikya tokens: local usage, read only")
    p.add_argument("--path", type=Path, help="Explicit project transcript directory; never scans unrelated projects")
    p.add_argument("--prices", type=Path, help="Optional user-provided USD/MTok JSON rate catalog")
    p.add_argument("--start-utc",help="Inclusive ISO timestamp for recorded project usage")
    p.add_argument("--end-utc",help="Exclusive ISO timestamp for recorded project usage")
    p.add_argument("--session-id",help="Select one recorded session")
    p.add_argument("--budget-tokens",type=int,help="Explicit local token budget, not account quota")
    p.add_argument("--cache-session",action="store_true",help="Cache this explicit session aggregate outside the project")
    p.add_argument("--root",type=Path,default=Path.cwd(),help="Project identity for the optional execution cache")
    args = p.parse_args()
    if args.path is None:
        p.error("--path is required to avoid reading unrelated projects")
    if not args.path.exists():
        p.error("transcript path not found")
    files = sorted(args.path.rglob("*.jsonl")) if args.path.is_dir() else [args.path]
    from aikya.middleware.metrics import aggregate_usage,budget_percentage
    report = aggregate_usage(files,args.start_utc,args.end_utc,args.session_id)
    if args.budget_tokens is not None:
        total=sum(report["totals"].get(k,0) for k in KEYS)
        report["local_budget"]={"recorded_tokens":total,"budget_tokens":args.budget_tokens,"used_percentage":budget_percentage(total,args.budget_tokens),"note":"Explicit local budget; not account quota or unique context size"}
    if args.cache_session:
        if not args.session_id:p.error("--cache-session requires --session-id")
        if args.start_utc or args.end_utc:p.error("An interval aggregate cannot replace the all-session display cache")
        from aikya.middleware.metrics import cache_usage
        cache_usage({"root":str(args.root.resolve()),"session_id":args.session_id},report)
    if args.prices:
        report["cost"] = estimate_cost(report, json.loads(args.prices.read_text(encoding="utf8")))
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
