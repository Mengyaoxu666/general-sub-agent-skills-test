"""Summarize anonymous root-model counts. Offline; no credentials or service access."""

import argparse
import json
import math
from pathlib import Path


def exact_keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("Unexpected or missing anonymous-schema fields")


def token_count(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Token counts must be finite nonnegative numbers")
    if not math.isfinite(value) or value < 0 or int(value) != value:
        raise ValueError("Token counts must be finite nonnegative integers")
    return int(value)


def totals(calls):
    if not isinstance(calls, list):
        raise ValueError("root_calls must be an array")
    result = {key: 0 for key in ("input", "output", "reasoning", "cache_read", "cache_write")}
    missing = 0
    for call in calls:
        if call is None:
            missing += 1
            continue
        exact_keys(call, ("input", "output", "reasoning", "cache"))
        exact_keys(call["cache"], ("read", "write"))
        for key in ("input", "output", "reasoning"):
            result[key] += token_count(call[key])
        for key in ("read", "write"):
            result["cache_" + key] += token_count(call["cache"][key])
    result["recorded_field_sum"] = sum(result.values())
    result["missing_calls"] = missing
    result["call_count"] = len(calls)
    return result


def validate_children(children):
    if not isinstance(children, list):
        raise ValueError("children must be an array")
    for child in children:
        exact_keys(child, ("root_calls",))
        totals(child["root_calls"])


def summarize(record):
    exact_keys(record, ("synthetic", "quality_passed", "arms"))
    if not isinstance(record["synthetic"], bool) or not isinstance(record["quality_passed"], bool):
        raise ValueError("Validation flags must be booleans")
    exact_keys(record["arms"], ("A", "B"))
    result = {"synthetic": record["synthetic"], "criterion": "root_model_only", "arms": {}}
    ready = record["quality_passed"]
    for arm in ("A", "B"):
        entry = record["arms"][arm]
        exact_keys(entry, ("complete", "root_calls", "children"))
        if not isinstance(entry["complete"], bool):
            raise ValueError("complete must be a boolean")
        validate_children(entry["children"])
        counts = totals(entry["root_calls"])
        result["arms"][arm] = counts
        ready = ready and entry["complete"] and counts["call_count"] > 0 and counts["missing_calls"] == 0
    a, b = [result["arms"][arm]["recorded_field_sum"] for arm in ("A", "B")]
    delta = (a - b) / a * 100 if a else None
    result["recorded_difference_percent"] = delta
    result["exact_reduction_percent"] = delta if ready and a else None
    result["status"] = "counts_and_declared_gate_complete" if ready and a else "not_validated"
    result["quality_warning"] = "quality_passed is supplied by the caller, not independently verified by this tool"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Anonymous JSON in the documented schema")
    args = parser.parse_args()
    try:
        result = summarize(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError, OverflowError):
        parser.exit(2, "Invalid anonymous input; values and paths are not echoed.\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
