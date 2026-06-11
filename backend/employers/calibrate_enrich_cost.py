"""Isolated cost calibration for the grounding-heavy enrichment call.

Measures the dominant cost unit — one grounded gemini-2.5-flash website-find
call — on a small sample of real (new Bay) employers, capturing token usage and
confirming a grounding request actually occurs. Writes NOTHING to employers.json
(safe against concurrent pipeline runs). The cheap, non-grounding enrich stages
(describe/occupations/classify ≈ $0.005/employer of tokens) are taken from the
prior measured calibration; this script freshly measures the part that dominates
and that the prior run can't speak to (current model + grounding behavior).

  python -m employers.calibrate_enrich_cost [N]
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Current Gemini pricing (verified 2026-06): grounding $35 / 1,000 grounded
# prompts (1,500/day free, shared); gemini-2.5-flash tokens.
PRICE_GROUNDING_PER_K = 35.0
PRICE_IN_PER_M = 0.30
PRICE_OUT_PER_M = 2.50


def _sample(n: int) -> list[dict]:
    seen, out = set(), []
    for fp in sorted(glob.glob(str(Path(__file__).parent / "cache" / "edd_county_*_f.json"))):
        for e in json.load(open(fp)):
            key = e["name"].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(e)
            if len(out) >= n:
                return out
    return out


def _prompt(e: dict) -> str:
    return (
        f"Find the official company website URL for this employer.\n"
        f"Name: {e['name']}\n"
        f"Location: {e.get('city','')}, CA\n"
        f"Industry: {e.get('naics_label') or e.get('naics4','')}\n"
        f"Use Google Search. Return only the homepage URL."
    )


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    if not os.environ.get("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY not loaded from .env")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[tool], temperature=0.0)

    rows = []
    for e in _sample(n):
        t0 = time.time()
        try:
            r = client.models.generate_content(
                model="gemini-2.5-flash", contents=_prompt(e), config=config
            )
        except Exception as ex:  # noqa: BLE001
            print(f"  FAIL {e['name'][:30]}: {type(ex).__name__}: {ex}")
            continue
        u = r.usage_metadata
        cand = (r.candidates or [None])[0]
        grounded = bool(getattr(cand, "grounding_metadata", None))
        pin = u.prompt_token_count or 0
        pout = u.candidates_token_count or 0
        tok_cost = pin * PRICE_IN_PER_M / 1e6 + pout * PRICE_OUT_PER_M / 1e6
        gnd_cost = PRICE_GROUNDING_PER_K / 1000 if grounded else 0.0
        rows.append({
            "name": e["name"], "grounded": grounded,
            "in": pin, "out": pout, "total": u.total_token_count or 0,
            "tok_cost": tok_cost, "gnd_cost": gnd_cost,
            "cost": tok_cost + gnd_cost, "sec": round(time.time() - t0, 1),
        })
        time.sleep(0.4)

    if not rows:
        raise SystemExit("no successful calls")
    n = len(rows)
    g = sum(r["grounded"] for r in rows)
    avg_tok = sum(r["tok_cost"] for r in rows) / n
    avg_gnd = sum(r["gnd_cost"] for r in rows) / n
    avg = sum(r["cost"] for r in rows) / n
    avg_in = sum(r["in"] for r in rows) / n
    avg_out = sum(r["out"] for r in rows) / n

    print(f"\n{'name':32} {'grnd':4} {'in':>6} {'out':>5} {'$/call':>8}")
    for r in rows:
        print(f"{r['name'][:32]:32} {'Y' if r['grounded'] else 'n':4} {r['in']:6d} {r['out']:5d} {r['cost']:8.4f}")
    print("-" * 60)
    print(f"sample={n}  grounded={g}/{n}  avg_in={avg_in:.0f}  avg_out={avg_out:.0f}")
    print(f"avg website-find call: tokens ${avg_tok:.4f} + grounding ${avg_gnd:.4f} = ${avg:.4f}")
    print(f"\nNOTE: this is the grounded website-find call only (the dominant unit).")
    print(f"Full per-employer adds the prior-measured cheap stages (~$0.005 tokens,")
    print(f"+1 grounded identity-probe in enrich). Grounding is $0 within the 1,500/day free quota.")


if __name__ == "__main__":
    main()
