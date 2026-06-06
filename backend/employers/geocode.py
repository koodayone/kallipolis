"""Geocode employer street addresses → lat/lng via the free US Census geocoder.

The EDD scrape gives each employer a street address but no coordinates; the
SVAMP employer map needs lat/lng. This is a one-time, idempotent enrichment:
it reads `employers.json`, geocodes the addressed employers, and writes a
DECOUPLED cache keyed by the stable EDD `emp_id` so it survives regeneration of
employers.json (the loader joins it back by emp_id). Re-running skips anything
already cached.

Scope defaults to the in-region advanced manufacturing set (the SVAMP employer
universe) but `--region` / `--sector` generalize it. The Census geocoder is
free and needs no key; we use the single-address endpoint (a few dozen calls),
built from the structured address fields rather than the loose `full` string.

    python3 employers/geocode.py                 # Bay + Advanced Manufacturing
    python3 employers/geocode.py --region Bay --sector "Advanced Manufacturing"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
EMPLOYERS = _HERE / "employers.json"
CACHE = _HERE / "geocode_cache.json"

_CENSUS = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
_BENCHMARK = "Public_AR_Current"


def _clean_address(addr: dict) -> str | None:
    """Build a clean 'street, city, ST zip' string from the structured fields —
    more reliable for the Census parser than the loose `full` (which can lack a
    comma before the city and carries a trailing-dash zip)."""
    street, city, state = addr.get("street"), addr.get("city"), addr.get("state")
    if not (street and city and state):
        return None
    # Drop suite/unit (the building geocodes the same) and expand a couple of
    # EDD abbreviations the geocoders choke on.
    street = re.sub(r"\s+(#|ste\.?|suite|unit|bldg|fl)\s*\S+\s*$", "", street, flags=re.I)
    street = re.sub(r"\bGrt\b", "Great", street, flags=re.I)
    zip5 = (addr.get("zip") or "").split("-")[0].strip()
    return f"{street}, {city}, {state} {zip5}".strip().rstrip(",")


def _geocode_nominatim(address: str) -> dict | None:
    """OSM/Nominatim fallback — more tolerant of street-range gaps than Census's
    exact matcher. Free; policy requires a User-Agent and ≤1 req/sec (enforced by
    the caller's sleep)."""
    q = urllib.parse.urlencode(
        {"q": address, "format": "json", "limit": 1, "countrycodes": "us"}
    )
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{q}",
        headers={"User-Agent": "kallipolis-geocode/1.0 (regional workforce mapping)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except Exception as e:
        print(f"    ! nominatim error: {e}", flush=True)
        return None
    if not data:
        return None
    return {"lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]),
            "matched": data[0].get("display_name")}


def _geocode(address: str) -> dict | None:
    """One Census lookup → {lat, lng, matched} or None on no-match/error."""
    q = urllib.parse.urlencode(
        {"address": address, "benchmark": _BENCHMARK, "format": "json"}
    )
    try:
        with urllib.request.urlopen(f"{_CENSUS}?{q}", timeout=20) as r:
            data = json.load(r)
    except Exception as e:  # network / parse — caller logs + continues
        print(f"    ! request error: {e}", flush=True)
        return None
    matches = (data.get("result") or {}).get("addressMatches") or []
    if not matches:
        return None
    c = matches[0].get("coordinates") or {}
    if c.get("y") is None or c.get("x") is None:
        return None
    return {"lat": c["y"], "lng": c["x"], "matched": matches[0].get("matchedAddress")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="Bay")
    ap.add_argument("--sector", default="Advanced Manufacturing")
    ap.add_argument("--sleep", type=float, default=0.2, help="seconds between calls")
    args = ap.parse_args()

    employers = json.loads(EMPLOYERS.read_text())
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    in_scope = [
        e for e in employers
        if args.region in (e.get("regions") or [])
        and args.sector in (e.get("swp_sectors") or [])
        and (e.get("address") or {}).get("emp_id")
        and _clean_address(e.get("address") or {})
    ]
    todo = [e for e in in_scope if (e["address"]["emp_id"] not in cache)]
    print(
        f"{args.region} ∩ {args.sector}: {len(in_scope)} addressable employers; "
        f"{len(cache)} already cached; {len(todo)} to geocode.",
        flush=True,
    )

    ok = fail = 0
    failures: list[str] = []
    for i, e in enumerate(todo, 1):
        emp_id = e["address"]["emp_id"]
        addr = _clean_address(e["address"])
        print(f"  [{i}/{len(todo)}] {e['name'][:36]:36} {addr}", flush=True)
        res, src = _geocode(addr), "census"
        if not res:
            res, src = _geocode_nominatim(addr), "nominatim"
            time.sleep(1.0)  # Nominatim policy: ≤1 req/sec
        if res:
            cache[emp_id] = {
                "lat": res["lat"], "lng": res["lng"],
                "matched": res["matched"], "name": e["name"], "source": src,
            }
            ok += 1
        else:
            fail += 1
            failures.append(f"{e['name']} — {addr}")
        CACHE.write_text(json.dumps(cache, indent=2))  # incremental: durable mid-run
        time.sleep(args.sleep)

    print(f"\nGeocoded {ok}, failed {fail}. Cache now holds {len(cache)} employers.", flush=True)
    if failures:
        print("Failed to geocode (no Census match):", flush=True)
        for f in failures:
            print(f"  - {f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
