"""Merge Claude-Code-resolved Bay websites into employers.json.

Reads the per-chunk outputs from the website-find workflow
(/tmp/bay_chunks/out_*.json), keyed by emp_id, and applies them to the Bay
employers that lacked a website. Conservative by design:
  - "high"  -> write `website = url` (the node carries only verified URLs)
  - "low"   -> leave `website = null`, candidate URL goes to the review queue
  - "none"  -> leave `website = null`, drop candidate -> review queue
Everything non-high, plus every chain outlet, is written to a review file for
human triage. Idempotent and backs up first.

  python -m employers.merge_bay_websites
"""

from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).parent
EMPLOYERS = _DIR / "employers.json"
REVIEW = _DIR / "bay_website_review.json"


def main() -> None:
    res: dict[str, dict] = {}
    for fp in glob.glob("/tmp/bay_chunks/out_*.json"):
        for r in json.load(open(fp)):
            if r.get("emp_id"):
                res[str(r["emp_id"])] = r

    employers = json.load(open(EMPLOYERS))
    backup = _DIR / "employers.pre-bay-website-merge.json"
    if not backup.exists():
        json.dump(employers, open(backup, "w"), indent=2)
        print(f"backed up -> {backup.name}")

    wrote_url = matched = 0
    review: list[dict] = []
    for e in employers:
        if "Bay" not in (e.get("regions") or []) or e.get("website"):
            continue
        eid = str((e.get("address") or {}).get("emp_id") or "")
        r = res.get(eid)
        if not r:
            continue
        matched += 1
        conf = r.get("confidence")
        if conf == "high":
            e["website"] = r.get("url")
            e["website_source"] = "claude_websearch"
            wrote_url += 1
        else:
            # low / none -> attempted, leave website null for human review
            e["website"] = None
            e["website_source"] = "claude_websearch"
        if conf != "high" or r.get("chain"):
            review.append({
                "emp_id": eid, "name": e["name"], "confidence": conf,
                "candidate_url": r.get("url"), "drop": r.get("drop", False),
                "chain": r.get("chain", False), "note": r.get("note"),
            })

    json.dump(employers, open(EMPLOYERS, "w"), indent=2)
    json.dump(review, open(REVIEW, "w"), indent=2)

    print(f"matched {matched}/{len(res)} resolved employers to Bay nodes")
    print(f"  wrote website URL (high-confidence): {wrote_url}")
    print(f"  review queue (low/none/chain): {len(review)} -> {REVIEW.name}")
    print(f"  breakdown: {dict(Counter(r['confidence'] for r in review))}, "
          f"chains={sum(1 for r in review if r['chain'])}, "
          f"drop_candidates={sum(1 for r in review if r['drop'])}")


if __name__ == "__main__":
    main()
