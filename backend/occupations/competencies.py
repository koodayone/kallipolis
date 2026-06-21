"""O*NET occupational competencies (Knowledge / Skills / Abilities / Technology)
— the authoritative POOL a report's competency section is curated from.

Deliberately NOT ingested into the graph: competencies are a report-layer concern
(no dashboard consumer), so they live as a bundled file read at report time rather
than as Occupation-node properties (which would be speculative L1 surface). The
report's curation skill reads this pool and selects the resonant few for a given
role; the bundle keeps that selection ANCHORED to real O*NET elements, so the
"Source: O*NET" citation stays honest — the LLM curates from authority, it does
not invent competencies from memory.

The authoritative source is O*NET (U.S. Dept. of Labor) — the same release (28.3)
the descriptions module bundles, at `backend/ontology/data/onet_competencies.tsv`
(public-domain, slow cadence, no runtime network fetch).

The subset is NOT raw top-importance — that surfaces generic boilerplate (every
occupation rates "English Language" and "Near Vision" highly). It is ranked by
**distinctiveness**: a competency's importance for the occupation MINUS its mean
importance across all occupations (its "lift" above the baseline) — what makes the
occupation *particular* (Chemistry for semiconductor processing, Control Precision
for mechatronics). Technology is the O*NET commodity-title categories, hot-tech and
rarer first, near-universal office tools dropped. Each SOC carries a top-N POOL the
report proposes and the curation step trims (data proposes, human/skill confirms).
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

BUNDLE_PATH = (
    Path(__file__).parent.parent / "ontology" / "data" / "onet_competencies.tsv"
)
CATEGORIES = ("knowledge", "skills", "abilities", "technology")

_by_soc: dict[str, dict[str, list[str]]] | None = None


def _load() -> dict[str, dict[str, list[str]]]:
    """``{base_soc -> {category -> [elements ranked]}}`` from the bundled TSV."""
    global _by_soc
    if _by_soc is not None:
        return _by_soc
    out: dict[str, dict[str, list[str]]] = defaultdict(lambda: {c: [] for c in CATEGORIES})
    with open(BUNDLE_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[row["soc_code"]][row["category"]].append(row["element"])
    _by_soc = dict(out)
    logger.info("Loaded O*NET competencies for %d SOCs", len(_by_soc))
    return _by_soc


def get_competencies(soc_code: str) -> dict[str, list[str]] | None:
    """``{knowledge, skills, abilities, technology}`` for a SOC, or None."""
    return _load().get(soc_code)


# ── Bundle maintenance (run once against an O*NET release to regenerate) ───────
def build_bundle(onet_dir: str, top_n: int = 8, im_floor: float = 2.5) -> None:
    """Regenerate `onet_competencies.tsv` from an O*NET text-DB release directory
    (e.g. db_28_3_text). Ranks K/S/A by distinctiveness (importance lift above the
    cross-occupation baseline, ≥ im_floor); technology by hot-tech/rarity, dropping
    titles common to >30% of occupations. Prefer the `.00` parent row; fall back to
    the first specialty for SOCs lacking one."""
    import statistics

    def ksa(fname: str) -> dict[str, list[str]]:
        rows: dict[str, dict[str, float]] = defaultdict(dict)
        allvals: dict[str, list[float]] = defaultdict(list)
        with open(f"{onet_dir}/{fname}", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                if row["Scale ID"] != "IM":
                    continue
                if row.get("Recommend Suppress") == "Y" or row.get("Not Relevant") == "Y":
                    continue
                try:
                    v = float(row["Data Value"])
                except ValueError:
                    continue
                rows[row["O*NET-SOC Code"]][row["Element Name"]] = v
                allvals[row["Element Name"]].append(v)
        mean = {el: statistics.fmean(vs) for el, vs in allvals.items()}
        primary, fallback = {}, {}
        for code, els in rows.items():
            base, suffix = code[:7], code[8:]
            ranked = sorted(((v - mean[el], el) for el, v in els.items() if v >= im_floor),
                            key=lambda x: -x[0])
            picks = [el for _, el in ranked][:top_n]
            (primary if suffix == "00" else fallback).setdefault(base, picks)
        return {**fallback, **primary}

    def tech() -> dict[str, list[str]]:
        rows: dict[str, dict[str, bool]] = defaultdict(dict)
        df: dict[str, int] = defaultdict(int)
        seen: dict[str, set] = defaultdict(set)
        with open(f"{onet_dir}/Technology Skills.txt", encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                t, code = row["Commodity Title"], row["O*NET-SOC Code"]
                rows[code][t] = rows[code].get(t, False) or row.get("Hot Technology") == "Y"
                if t not in seen[code]:
                    df[t] += 1
                    seen[code].add(t)
        nsoc = len(rows)
        ubiquitous = {t for t, c in df.items() if c > 0.30 * nsoc}
        primary, fallback = {}, {}
        for code, titles in rows.items():
            base, suffix = code[:7], code[8:]
            cand = {t: hot for t, hot in titles.items() if t not in ubiquitous}
            ranked = sorted(cand.items(), key=lambda x: (not x[1], df[x[0]], x[0]))
            picks = [t for t, _ in ranked][:top_n]
            (primary if suffix == "00" else fallback).setdefault(base, picks)
        return {**fallback, **primary}

    cats = {"knowledge": ksa("Knowledge.txt"), "skills": ksa("Skills.txt"),
            "abilities": ksa("Abilities.txt"), "technology": tech()}
    socs = sorted(set().union(*(set(c) for c in cats.values())))
    with open(BUNDLE_PATH, "w", encoding="utf-8") as f:
        f.write("soc_code\tcategory\trank\telement\n")
        for soc in socs:
            for cat in CATEGORIES:
                for i, el in enumerate(cats[cat].get(soc, [])):
                    f.write(f"{soc}\t{cat}\t{i + 1}\t{el}\n")
    print(f"wrote {BUNDLE_PATH} for {len(socs)} SOCs")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:  # regenerate the bundle from an O*NET release dir
        build_bundle(sys.argv[1])
    else:  # quick inspection of the curation pool for a few SOCs
        for soc in ("51-9141", "17-3026", "17-3024"):
            print(soc, get_competencies(soc))
