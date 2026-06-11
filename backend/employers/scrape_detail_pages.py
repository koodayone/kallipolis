"""Scrape EDD empDetails pages for the already-scraped firms — capturing the
free structured fields the list-scrape (edd_scrape.py) discards: official
website, 6-digit NAICS, contact name+title, and phone.

Why (measured 2026-06-11 on a 39-firm stratified sample): the empDetails page
(Data Axle data surfaced through the EDD UI) lists the website for ~92% of
firms, the 6-digit NAICS for ~100% (which disambiguates sector WITHOUT an LLM —
the naics4-only scrape made AM look ~60% noise; at naics6 aerospace 3364xx,
medical 339112, metal-fab 3323xx all separate cleanly), and a CEO/owner-level
contact for ~92% — all free. The prior pipeline paid Gemini grounding to
recover websites EDD already lists, never captured naics6, and never produced a
contact at all. This pass deletes most of that cost.

Additive over the list-scrape caches (cache/edd_county_*_f.json), which already
carry emp_id + geog_area — the keys the detail URL needs. Results land in
cache/detail_pages.json keyed by emp_id; downstream joins by emp_id.

Design (project long-running-job conventions):
  * Resumable: emp_ids already in detail_pages.json are skipped.
  * Observable: progress + running fill-rate every 25 firms, flushed.
  * Incremental: detail_pages.json rewritten every 25 firms.
  * Fail-fast: aborts on 10 consecutive failures (site down / parser broke).
  * Polite: 0.4s between requests; verify=False (EDD's cert chain doesn't validate).

Usage:
    python3 -m employers.scrape_detail_pages [--county santa_clara] [--limit N]
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import re
import sys
import time
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

_DIR = Path(__file__).parent
_CACHE = _DIR / "cache"
_DETAIL_OUT = _CACHE / "detail_pages.json"
_DETAIL_URL = (
    "https://labormarketinfo.edd.ca.gov/aspdotnet/databrowsing/"
    "empDetails.aspx?menuChoice=emp&empid={eid}&geogArea={geo}"
)
_HDR = {"User-Agent": "Mozilla/5.0"}
_PLACEHOLDER = {"", "N/A", "NOT LISTED", "NOT AVAILABLE", "NONE", "NOT REPORTED"}
_NAICS6 = re.compile(r"NAICS code:\s*(\d{6})")


def _parse(h: str) -> dict:
    """Pull the labelled fields out of the empDetails HTML. Labels and values
    sit on adjacent lines once tags are stripped; 'Not Listed' ⇒ absent."""
    t = re.sub(r"<(script|style).*?</\1>", " ", h, flags=re.S | re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    lines = [x.strip() for x in t.splitlines() if x.strip()]

    def val(label: str):
        for i, l in enumerate(lines):
            if l.rstrip(":") == label or l.startswith(label):
                rest = l.split(":", 1)[1].strip() if ":" in l else ""
                v = (rest or (lines[i + 1] if i + 1 < len(lines) else "")).strip()
                return None if v.upper() in _PLACEHOLDER else v
        return None

    contact = val("Contact")
    name = title = None
    if contact:
        parts = [p.strip() for p in contact.split(",", 1)]
        name = parts[0] or None
        title = parts[1] if len(parts) > 1 else None
    m = _NAICS6.search(h)
    return {
        "website": val("Website"),
        "naics6": m.group(1) if m else None,
        "contact_name": name,
        "contact_title": title,
        "phone": val("Telephone"),
    }


def _load_firms(county_filter: str | None) -> dict:
    firms: dict[str, dict] = {}
    for fp in sorted(_CACHE.glob("edd_county_*_f.json")):
        county = fp.stem.replace("edd_county_", "")[:-2]
        if county_filter and county != county_filter:
            continue
        for r in json.loads(fp.read_text()):
            eid, geo = r.get("emp_id"), r.get("geog_area")
            if eid and geo and eid not in firms:
                firms[eid] = {"name": r.get("name"), "geog_area": geo, "county": county}
    return firms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--county", help="restrict to one county (cache stem, e.g. santa_clara)")
    ap.add_argument("--limit", type=int, help="cap firms this run (for validation)")
    args = ap.parse_args()

    firms = _load_firms(args.county)
    out = json.loads(_DETAIL_OUT.read_text()) if _DETAIL_OUT.exists() else {}
    todo = [eid for eid in firms if eid not in out]
    if args.limit:
        todo = todo[: args.limit]
    print(f"firms total={len(firms)}  already done={len(out)}  to fetch={len(todo)}", flush=True)

    done = fails = consec = 0
    fill = {"website": 0, "naics6": 0, "contact_name": 0, "phone": 0}
    for i, eid in enumerate(todo, 1):
        f = firms[eid]
        try:
            resp = requests.get(
                _DETAIL_URL.format(eid=eid, geo=f["geog_area"]),
                verify=False, timeout=20, headers=_HDR,
            )
            d = _parse(resp.text)
            d["county"] = f["county"]
            out[eid] = d
            done += 1
            consec = 0
            for k in fill:
                if d.get(k):
                    fill[k] += 1
        except Exception as e:  # noqa: BLE001
            fails += 1
            consec += 1
            if consec >= 10:
                _DETAIL_OUT.write_text(json.dumps(out))
                sys.exit(f"ABORT: {consec} consecutive failures ({type(e).__name__}: {e}) — site down or parser broke")
        if i % 25 == 0 or i == len(todo):
            _DETAIL_OUT.write_text(json.dumps(out))
            pr = lambda k: f"{100 * fill[k] // done}%" if done else "—"
            print(
                f"  {i}/{len(todo)}  done={done} fail={fails}  "
                f"web={pr('website')} naics6={pr('naics6')} contact={pr('contact_name')} phone={pr('phone')}",
                flush=True,
            )
        time.sleep(0.4)

    _DETAIL_OUT.write_text(json.dumps(out))
    print(f"\nDONE. detail records: {len(out)} → {_DETAIL_OUT}", flush=True)
    if done:
        print("fill rates this run:", {k: f"{100 * fill[k] // done}%" for k in fill}, flush=True)


if __name__ == "__main__":
    main()
