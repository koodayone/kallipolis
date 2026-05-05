"""For Foothill's direct-CTE supported SOCs, show:
  Part 1: current top-10 partnership candidates (sort by pct_total)
  Part 2: missing NAICS that would enter the top tier if scraped —
          the enhancement hypothesis.

Direct-CTE = Strong CTE + Moderate CTE education bands.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

import openpyxl
from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology import oes as _oes
from ontology.oes import oes_socs_for_naics4
from employers.edd_scrape import CTE_NAICS_CODES

COLLEGE = "Foothill College"
TOP_N = 10
HYPOTHESIS_TOP_N = 10


def _load_naics_titles() -> dict[str, str]:
    wb = openpyxl.load_workbook(_oes.OES_NAICS4_PATH, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {c: i for i, c in enumerate(header)}
    titles: dict[str, str] = {}
    for row in rows:
        if not row: continue
        n = row[cols["NAICS"]]; t = row[cols["NAICS_TITLE"]]
        if n is None or t is None: continue
        s = str(n).strip()
        if len(s) == 6 and s.isdigit():
            titles.setdefault(s[:4], str(t))
    wb.close()
    return titles


def _load_education() -> dict[str, str]:
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["SOC"] and row.get("Typical Entry Level Education"):
                edu.setdefault(row["SOC"], row["Typical Entry Level Education"].strip())
    return edu


def _band(level: str) -> str:
    if level in {"Postsecondary nondegree award", "Associate's degree"}: return "Strong CTE"
    if level in {"High school diploma or equivalent", "Some college, no degree",
                 "No formal educational credential"}: return "Moderate CTE"
    return "Other"


def main(out_path: str) -> None:
    edu_by_soc = _load_education()
    naics_titles = _load_naics_titles()
    _oes._ensure_loaded()

    # Build SOC → ranked NAICS list (any pct_total > 0).
    soc_to_naics: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for naics4, rows in _oes._socs_by_naics4.items():
        for r in rows:
            pct = r.get("pct_total") or 0.0
            if pct > 0:
                soc_to_naics[r["soc"]].append((naics4, pct))
    for soc in soc_to_naics:
        soc_to_naics[soc].sort(key=lambda x: -x[1])

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        region = session.run(
            "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) RETURN r.name AS n",
            n=COLLEGE,
        ).single()["n"]
        supported = session.run(
            """
            MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
            RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
            """, col=COLLEGE,
        ).data()
        supported_socs = {r["soc"]: r["title"] for r in supported}
        emps = session.run(
            """
            MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
            WHERE e.naics4 IS NOT NULL
            OPTIONAL MATCH (e)-[:HIRES_FOR]->(o:Occupation)
            RETURN e.name AS name, e.naics4 AS naics4,
                   collect(DISTINCT o.soc_code) AS llm
            """, r=region,
        ).data()
    driver.close()

    # Filter to direct-CTE supported SOCs.
    direct_cte_socs = {
        soc: title for soc, title in supported_socs.items()
        if _band(edu_by_soc.get(soc, "")) in ("Strong CTE", "Moderate CTE")
    }

    # Per SOC, current candidate list under existing CTE_NAICS_CODES.
    per_soc: dict[str, list[dict]] = {}
    for emp in emps:
        if emp["naics4"] not in CTE_NAICS_CODES:
            continue  # Defensive — every regional employer should be in the list
        llm_set = set(emp["llm"])
        for r in oes_socs_for_naics4(emp["naics4"]):
            if r["soc"] not in direct_cte_socs: continue
            pct = r.get("pct_total") or 0.0
            if pct <= 0: continue
            per_soc.setdefault(r["soc"], []).append({
                "name": emp["name"],
                "naics4": emp["naics4"],
                "pct_total": pct,
                "llm_corr": r["soc"] in llm_set,
            })
    for soc in per_soc:
        per_soc[soc].sort(key=lambda c: (-c["pct_total"], c["name"]))

    # Per SOC, missing NAICS — those in soc_to_naics but not in CTE_NAICS_CODES.
    missing_per_soc: dict[str, list[tuple[str, float]]] = {}
    for soc in direct_cte_socs:
        all_ranked = soc_to_naics.get(soc, [])
        miss = [(n, p) for n, p in all_ranked if n not in CTE_NAICS_CODES]
        if miss:
            missing_per_soc[soc] = miss[:HYPOTHESIS_TOP_N]

    # ── Render ────────────────────────────────────────────────────────
    out: list[str] = []
    out.append(f"# Direct-CTE Partnership Candidates — {COLLEGE} ({region})\n\n")
    out.append(
        "Two views per occupation:\n\n"
        "1. **Current state**: top 10 regional employers under the "
        "existing methodology (NAICS 0% threshold, sorted by pct_total).\n"
        "2. **Enhancement hypothesis**: top NAICS-4 codes BLS publishes "
        "for this SOC that are *not* in the project's search list. "
        "If those NAICS were added to the EDD scrape and produced "
        "employers, those employers would slot into the candidate list "
        "at the indicated pct_total.\n\n"
        "Restricted to direct-CTE supported SOCs (Strong + Moderate "
        "education bands). NAICS labels from BLS OEWS NAICS_TITLE.\n\n"
    )

    out.append(f"## Universe\n\n")
    out.append(f"- Direct-CTE supported SOCs at {COLLEGE}: "
               f"**{len(direct_cte_socs)}**\n")
    strong = [s for s in direct_cte_socs
              if _band(edu_by_soc.get(s, "")) == "Strong CTE"]
    moderate = [s for s in direct_cte_socs
                if _band(edu_by_soc.get(s, "")) == "Moderate CTE"]
    out.append(f"  - Strong CTE: {len(strong)}\n")
    out.append(f"  - Moderate CTE: {len(moderate)}\n")
    served = sum(1 for s in direct_cte_socs if per_soc.get(s))
    out.append(f"- SOCs with ≥1 current candidate: **{served}** "
               f"({100*served/len(direct_cte_socs):.1f}%)\n")
    n_with_missing = sum(1 for s in direct_cte_socs if missing_per_soc.get(s))
    out.append(f"- SOCs with ≥1 missing top-NAICS that could enhance: "
               f"**{n_with_missing}** "
               f"({100*n_with_missing/len(direct_cte_socs):.1f}%)\n\n")

    # Distribution of "would benefit" types.
    big_gains = 0   # current 0 or 1 candidates AND missing top-NAICS exists
    upgrades = 0    # missing NAICS pct_total > current top pct_total
    reinforces = 0  # missing NAICS pct_total in current top range but not above
    minor = 0
    for soc in direct_cte_socs:
        cur = per_soc.get(soc, [])
        miss = missing_per_soc.get(soc, [])
        if not miss: continue
        miss_top_pct = miss[0][1]
        cur_top_pct = cur[0]["pct_total"] if cur else 0.0
        if len(cur) <= 1:
            big_gains += 1
        elif miss_top_pct > cur_top_pct:
            upgrades += 1
        elif miss_top_pct >= cur_top_pct * 0.5:
            reinforces += 1
        else:
            minor += 1
    out.append("## Enhancement impact distribution\n\n")
    out.append("| Impact | SOCs |\n|---|---:|\n")
    out.append(f"| Big gain (currently ≤1 candidate, missing NAICS would seed) | {big_gains} |\n")
    out.append(f"| Upgrade (missing NAICS exceeds current top pct_total) | {upgrades} |\n")
    out.append(f"| Reinforce (missing NAICS comparable to current top) | {reinforces} |\n")
    out.append(f"| Minor (missing NAICS well below current top) | {minor} |\n")

    # ── Per-SOC sections ──────────────────────────────────────────────
    out.append("\n---\n\n# Per-SOC views\n\n")
    out.append("Strong CTE SOCs first, then Moderate CTE. Within each band, "
               "ordered by descending current top pct_total (most-aligned "
               "occupations surface first).\n\n")

    for band_label, band_socs in [
        ("Strong CTE", strong),
        ("Moderate CTE", moderate),
    ]:
        out.append(f"\n## {band_label}  ({len(band_socs)} SOCs)\n")
        def _max_cur(soc):
            return per_soc.get(soc, [{"pct_total": 0}])[0]["pct_total"] \
                if per_soc.get(soc) else 0.0
        band_socs.sort(key=lambda s: (-_max_cur(s), s))

        for soc in band_socs:
            title = direct_cte_socs[soc]
            edu = edu_by_soc.get(soc, "")
            cur = per_soc.get(soc, [])
            miss = missing_per_soc.get(soc, [])
            cur_top_pct = cur[0]["pct_total"] if cur else 0.0

            out.append(f"\n### `{soc}` {title}\n")
            out.append(f"*{edu} · current candidates: {len(cur)}*\n\n")

            # Current state
            out.append("**Current top candidates** (sorted by pct_total):\n\n")
            if not cur:
                out.append("*No regional employer in any in-search-list NAICS "
                           "publishes this SOC at any pct_total > 0.*\n\n")
            else:
                shown = cur[:TOP_N]
                out.append("| pct_total | Employer | NAICS-4 | LLM |\n"
                           "|---:|---|---|:---:|\n")
                for c in shown:
                    mark = "✓" if c["llm_corr"] else " "
                    out.append(f"| {c['pct_total']:.1f}% | {c['name']} | "
                               f"{c['naics4']} | {mark} |\n")
                if len(cur) > TOP_N:
                    out.append(f"\n*... and {len(cur) - TOP_N} more*\n")

            # Hypothesis
            out.append("\n**Enhancement hypothesis** — missing NAICS:\n\n")
            if not miss:
                out.append("*No high-pct_total NAICS missing from the search "
                           "list. Current methodology already reaches the "
                           "structurally relevant industries for this SOC.*\n")
            else:
                out.append("| pct_total | NAICS-4 | Title | Impact vs current top |\n"
                           "|---:|---|---|---|\n")
                for n, p in miss:
                    label = naics_titles.get(n, "(no title)")
                    if not cur:
                        impact = f"would seed (currently empty)"
                    elif p > cur_top_pct:
                        impact = f"**exceeds** current top ({cur_top_pct:.1f}%)"
                    elif p >= cur_top_pct * 0.5:
                        impact = f"reinforces (current top: {cur_top_pct:.1f}%)"
                    else:
                        impact = f"adds to tail (current top: {cur_top_pct:.1f}%)"
                    out.append(f"| {p:.1f}% | `{n}` | {label} | {impact} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/direct_cte_with_hypothesis.md")
