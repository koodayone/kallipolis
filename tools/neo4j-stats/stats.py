"""Aggregate the Neo4j query timing JSONL log into a slow-query report.

Reads `backend/logs/neo4j_queries.jsonl` (or `--log <path>`) and prints
two tables:

  1. Per-fingerprint stats — cypher hash, count, p50, p95, max, total ms.
     Sorted by total_ms (cumulative wait time) by default; this is the
     right "what should I optimize first" ordering, since a 5ms query
     run 10K times costs more than a 2s query run twice.

  2. Per-endpoint stats — same shape, grouped by `request_ctx`.

Pass `--top N` to limit rows. Pass `--since <minutes>` to look at the
last N minutes only. Pass `--show-cypher` to print the cypher text for
each fingerprint (truncated).

Usage:
  python3 tools/neo4j-stats/stats.py
  python3 tools/neo4j-stats/stats.py --top 20 --since 60 --show-cypher
  python3 tools/neo4j-stats/stats.py --sort p95
"""

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path


def _default_log_path() -> Path:
    here = Path(__file__).resolve().parent.parent.parent
    return here / "backend" / "logs" / "neo4j_queries.jsonl"


_PATH_NUM = re.compile(r"/\d+(?=/|$)")
_PATH_UUID = re.compile(
    r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?=/|$)",
    re.IGNORECASE,
)


def _normalize_ctx(ctx: str) -> str:
    if not ctx:
        return "(background)"
    ctx = _PATH_UUID.sub("/{uuid}", ctx)
    ctx = _PATH_NUM.sub("/{id}", ctx)
    return ctx


def _percentile(values, pct):
    if not values:
        return 0
    if len(values) == 1:
        return values[0]
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def _fmt_ms(v):
    if v >= 1000:
        return f"{v/1000:.2f}s"
    return f"{v:.1f}ms"


def _summarize(events, sort_key):
    durations = [e["duration_ms"] for e in events]
    return {
        "count": len(events),
        "total_ms": sum(durations),
        "p50": _percentile(durations, 50),
        "p95": _percentile(durations, 95),
        "max": max(durations),
        "_events": events,
    }


def _print_table(title, groups, top, sort_key, show_cypher):
    print(f"\n=== {title} (sorted by {sort_key}) ===\n")
    rows = sorted(groups.items(), key=lambda kv: kv[1][sort_key], reverse=True)[:top]

    cols = ("count", "total_ms", "p50", "p95", "max")
    header_label = "fingerprint" if title.startswith("By fingerprint") else "endpoint"
    label_w = max(len(header_label), max((len(str(k)) for k, _ in rows), default=10))
    print(f"  {header_label:<{label_w}}  {'count':>7}  {'total':>10}  {'p50':>9}  {'p95':>9}  {'max':>9}")
    print("  " + "-" * (label_w + 2 + 7 + 2 + 10 + 2 + 9 + 2 + 9 + 2 + 9))
    for key, summary in rows:
        print(
            f"  {str(key):<{label_w}}  {summary['count']:>7}  "
            f"{_fmt_ms(summary['total_ms']):>10}  "
            f"{_fmt_ms(summary['p50']):>9}  "
            f"{_fmt_ms(summary['p95']):>9}  "
            f"{_fmt_ms(summary['max']):>9}"
        )
        if show_cypher and header_label == "fingerprint":
            sample = summary["_events"][0].get("cypher", "")
            print(f"      {sample[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, default=_default_log_path())
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--since", type=float, help="Restrict to last N minutes")
    ap.add_argument(
        "--sort",
        choices=("total_ms", "count", "p50", "p95", "max"),
        default="total_ms",
        help="Ordering for top-N",
    )
    ap.add_argument("--show-cypher", action="store_true")
    ap.add_argument("--ctx", help="Filter to events whose request_ctx contains this substring")
    args = ap.parse_args()

    if not args.log.exists():
        print(f"No log at {args.log}. Has the API served any requests?", file=sys.stderr)
        sys.exit(1)

    cutoff = (time.time() - args.since * 60) if args.since else None

    by_fp = defaultdict(list)
    by_ctx = defaultdict(list)
    total = 0
    skipped = 0
    fp_to_cypher = {}

    with args.log.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if cutoff is not None and event.get("ts", 0) < cutoff:
                continue
            if args.ctx and args.ctx not in event.get("request_ctx", ""):
                continue
            total += 1
            fp = event.get("fingerprint", "?")
            by_fp[fp].append(event)
            fp_to_cypher.setdefault(fp, event.get("cypher", ""))
            by_ctx[_normalize_ctx(event.get("request_ctx", ""))].append(event)

    if total == 0:
        print("No matching events.", file=sys.stderr)
        sys.exit(0)

    fp_summary = {fp: _summarize(events, args.sort) for fp, events in by_fp.items()}
    ctx_summary = {ctx: _summarize(events, args.sort) for ctx, events in by_ctx.items()}

    print(f"Loaded {total} events from {args.log}")
    if skipped:
        print(f"  ({skipped} malformed lines skipped)")

    _print_table("By fingerprint", fp_summary, args.top, args.sort, args.show_cypher)
    _print_table("By endpoint", ctx_summary, args.top, args.sort, False)


if __name__ == "__main__":
    main()
