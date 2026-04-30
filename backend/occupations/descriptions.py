"""
Resolve BLS SOC 2018 occupation definitions from the bundled O*NET file.

The authoritative descriptions for SOC codes are the BLS Standard
Occupational Classification 2018 definitions. BLS publishes them at
bls.gov/soc/2018; the file ships in-repo via O*NET, which redistributes
the BLS definitions verbatim on the `.00` rows of its Occupation Data
release. We bundle the O*NET TSV at
`backend/ontology/data/onet_occupation_data.tsv` (release 28.3) for the
same reason the other federal vocabulary files (TOP→CIP, CIP→SOC,
PCAH sectors, OES) are bundled: public-domain dataset, slow update
cadence, no live dependency on a network fetch at runtime.

The previous implementation in this module — a hand-curated dict of
~250 descriptions plus a regex template fallback — was replaced because
both halves drifted from BLS truth: the dict shipped 84 mismatched or
swapped entries, and the regex generator produced content-wrong
descriptions for non-trivial titles (e.g., Locomotive Engineers
described as a discipline of engineering rather than train-driving) and
vapid fallbacks ("Performs professional duties as a paperhangers") for
titles whose role-noun the regex did not recognize. Anchoring to BLS
removes the proxy.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ONET_TSV_PATH = (
    Path(__file__).parent.parent / "ontology" / "data" / "onet_occupation_data.tsv"
)


_soc_to_description: dict[str, str] | None = None


def _load_soc_descriptions() -> dict[str, str]:
    """Index O*NET Occupation Data by base SOC code.

    O*NET-SOC codes have the shape ``XX-XXXX.NN`` where ``.00`` carries
    the BLS SOC parent definition and ``.01``+ carry O*NET-specific
    specializations. We prefer ``.00``; if a SOC has only specialty
    rows we fall back to the first specialty so every BLS SOC in the
    file resolves to some description.
    """
    global _soc_to_description
    if _soc_to_description is not None:
        return _soc_to_description

    primary: dict[str, str] = {}  # .00 hits
    fallback: dict[str, str] = {}  # first specialty seen, used only if no .00

    with open(ONET_TSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            code = row["O*NET-SOC Code"]
            base = code[:7]  # "13-1041" from "13-1041.00"
            suffix = code[8:]
            description = row["Description"].strip()
            if not description:
                continue
            if suffix == "00":
                primary[base] = description
            elif base not in fallback:
                fallback[base] = description

    merged = {**fallback, **primary}
    _soc_to_description = merged
    logger.info(
        f"Loaded SOC 2018 definitions: {len(merged)} SOCs "
        f"({len(primary)} primary, {len(merged) - len(primary)} via specialty fallback)"
    )
    return merged


def get_description(soc_code: str) -> str | None:
    """Return the BLS SOC 2018 definition for a SOC, or None if unknown."""
    return _load_soc_descriptions().get(soc_code)


def update_descriptions() -> None:
    """Rewrite occupations.json descriptions from the bundled O*NET file."""
    import json

    path = Path(__file__).parent / "occupations.json"
    with open(path) as f:
        occupations = json.load(f)

    updated = 0
    missing: list[str] = []
    for occ in occupations:
        new_desc = get_description(occ["soc_code"])
        if new_desc is None:
            missing.append(occ["soc_code"])
            continue
        if new_desc != occ.get("description"):
            occ["description"] = new_desc
            updated += 1

    with open(path, "w") as f:
        json.dump(occupations, f, indent=2)

    print(f"Updated {updated}/{len(occupations)} descriptions")
    if missing:
        print(f"WARNING: {len(missing)} SOCs not found in O*NET file:")
        for soc in missing:
            print(f"  {soc}")

    samples = ["13-1041", "53-4011", "29-1141", "47-2111", "31-9011"]
    for soc in samples:
        occ = next((o for o in occupations if o["soc_code"] == soc), None)
        if occ:
            print(f"\n  {occ['title']} ({soc})")
            print(f"  → {occ['description']}")


if __name__ == "__main__":
    update_descriptions()
