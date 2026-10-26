"""Pure transcript aggregation and explicit historical price estimates."""
import json
from collections import defaultdict
from pathlib import Path

KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


def estimate_haiku_55_request(usage: dict) -> dict:
    """Anthropic API list-price bounds, not billed costs.

    A prompt above 100K is priced at the higher tier for all the usage in
    that request. Creation cache TTL can be 5m or 1h, so absent breakdown
    the method returns a range rather than an invented exact invoice.
    """
    values = {}
    for key in KEYS:
        value = usage.get(key, 0)
        if type(value) is not int or value < 0:
            raise ValueError("usage values must be nonnegative integers")
        values[key] = value
    prompt = (values["input_tokens"] + values["cache_creation_input_tokens"] +
              values["cache_read_input_tokens"])
    large = prompt > 100_000
    inp, out = (0.50, 2.50) if large else (0.10, 0.50)
    cache_read, write_5m, write_1h = ((0.05, 0.625, 1.00) if large
                                     else (0.01, 0.125, 0.20))
    base = (values["input_tokens"] * inp + values["output_tokens"] * out +
            values["cache_read_input_tokens"] * cache_read) / 1_000_000
    created = values["cache_creation_input_tokens"] / 1_000_000
    return {"prompt_tokens": prompt, "pricing_tier": "over_100k" if large else "up_to_100k",
            "minimum_usd": round(base + created * write_5m, 8),
            "maximum_usd": round(base + created * write_1h, 8),
            "note": "Estimated Anthropic API list price (5m–1h cache writes). Not billing."}

def summarize(paths, *, event_filter=None):
    totals = defaultdict(int)
    models = defaultdict(lambda: defaultdict(int))
    sessions = set()
    calls = {}
    call_models = {}
    contexts = []
    tool_outputs = []
    tool_events = set()
    stop_blocks = 0
    missing_usage = 0
    for path in paths:
        try:
            with path.open(encoding="utf8") as fh:
                for line in fh:
                    try:
                        event = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    if not isinstance(event, dict):
                        continue
                    msg = event.get("message")
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") == "user":
                        content = msg.get("content", [])
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "tool_result":
                                    size = len(str(block.get("content", "")).encode("utf8"))
                                    tool_id = str(block.get("tool_use_id", "unknown"))
                                    marker = (str(path), str(event.get("uuid") or ""), tool_id)
                                    if marker not in tool_events:
                                        tool_events.add(marker)
                                        tool_outputs.append({"bytes": size, "tool_use_id": tool_id})
                    # Count only explicitly recorded stop-hook decisions, never infer them.
                    if event.get("hook_event_name") == "Stop" and event.get("decision") == "block":
                        stop_blocks += 1
                    if msg.get("role") != "assistant":
                        continue
                    if event_filter is not None and not event_filter(event,path):continue
                    usage = msg.get("usage")
                    if not isinstance(usage, dict):
                        missing_usage += 1
                        continue
                    identity = msg.get("id") or event.get("uuid")
                    dedup = (str(event.get('sessionId') or event.get('session_id') or path), str(identity)) if identity else None
                    model = str(msg.get("model") or "unknown")
                    # Streamed transcript snapshots reuse the same message id.
                    # Keep the largest cumulative usage per category.
                    current = {k: v for k in KEYS
                               if type(v := usage.get(k, 0)) is int and v >= 0}
                    if dedup:
                        call_models[dedup] = model
                        old = calls.get(dedup, {})
                        for key, value in current.items():
                            delta = max(0, value - old.get(key, 0))
                            totals[key] += delta
                            models[model][key] += delta
                        if not old:
                            totals["calls"] += 1
                        calls[dedup] = {key: max(current.get(key, 0), old.get(key, 0))
                                        for key in KEYS}
                    else:
                        totals["calls"] += 1
                        for key, value in current.items():
                            totals[key] += value
                            models[model][key] += value
                    sessions.add(str(path))
                    if "input_tokens" in current:
                        context = sum(current.get(k, 0) for k in (
                            "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                        contexts.append(context)
        except (OSError, UnicodeError):
            continue
    haiku_records = [estimate_haiku_55_request(usage) for identity, usage in calls.items()
                     if call_models.get(identity) == "claude-haiku-5-5"]
    haiku_range = {"calls_with_ids": len(haiku_records),
                   "minimum_usd": round(sum(x["minimum_usd"] for x in haiku_records), 8),
                   "maximum_usd": round(sum(x["maximum_usd"] for x in haiku_records), 8),
                   "scope": "Anthropic API list-price estimate for identified Haiku 5.5 messages only; excludes unkeyed events"}
    return {
        "haiku_55_estimated_api_cost": haiku_range,
        "sessions_with_usage": len(sessions),
        "usage_records_missing": missing_usage,
        "totals": dict(totals),
        "models": {key: dict(value) for key, value in sorted(models.items())},
        "context_observations": {
            "first": contexts[0] if contexts else None,
            "mean": round(sum(contexts) / len(contexts)) if contexts else None,
            "max": max(contexts) if contexts else None,
            "note": "Per transcript occurrence, not a distinct request or window-size guarantee."
        },
        "largest_tool_results": sorted(tool_outputs, key=lambda v: v["bytes"], reverse=True)[:10],
        "stop_blocks_explicitly_recorded": stop_blocks,
        "note": "Local usage estimates only. No content is printed; model/provider prices and actual invoice are not inferred."
    }
