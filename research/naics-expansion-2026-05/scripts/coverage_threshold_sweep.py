"""Per-college coverage analysis under multiple pct_total thresholds.

Tests the proposition: a pct_total ≥ 1% filter on NAICS-matrix
employer-occupation linkage produces a partnership-candidate pool with
defensible signal. Sweeps thresholds 0.5%/1%/2%/5%, restricts to
direct-CTE education bands (where the alignment claim lives), and
cross-tabs against LLM-curated to show complementarity.

Outputs a single markdown report summarizing all 8 loaded colleges.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

from ontology.crosswalks import COE_DEMAND_PATH
from ontology.oes import oes_socs_for_naics4

THRESHOLDS = [0.5, 1.0, 2.0, 5.0]

CTE_STRONG = {
    "Postsecondary nondegree award",
    "Associate's degree",
}
CTE_MODERATE = {
    "High school diploma or equivalent",
    "Some college, no degree",
    "No formal educational credential",
}
DIRECT_CTE = CTE_STRONG | CTE_MODERATE


def _load_education_for_socs() -> dict[str, str]:
    edu: dict[str, str] = {}
    with open(COE_DEMAND_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["SOC"] and row.get("Typical Entry Level Education"):
                edu.setdefault(row["SOC"], row["Typical Entry Level Education"].strip())
    return edu


def _band(level: str) -> str:
    if level in CTE_STRONG: return "Strong CTE"
    if level in CTE_MODERATE: return "Moderate CTE"
    if level == "Bachelor's degree": return "Bachelor's"
    if level in {"Master's degree", "Doctoral or professional degree"}: return "Master's+"
    return "Unknown"


def analyze_college(session, college: str, edu_by_soc: dict[str, str]) -> dict:
    region = session.run(
        "MATCH (c:College {name: $n})-[:IN_MARKET]->(r:Region) RETURN r.name AS name",
        n=college,
    ).single()
    if not region:
        return {}
    region = region["name"]

    supported = session.run(
        """
        MATCH (c:Course {college: $col})-[:PREPARES_FOR]->(occ:Occupation)
        RETURN DISTINCT occ.soc_code AS soc, occ.title AS title
        """, col=college,
    ).data()
    supported_socs = {r["soc"]: r["title"] for r in supported}

    employers = session.run(
        """
        MATCH (e:Employer)-[:IN_MARKET]->(:Region {name: $r})
        WHERE e.naics4 IS NOT NULL
        OPTIONAL MATCH (e)-[:HIRES_FOR]->(o:Occupation)
        RETURN e.name AS name, e.naics4 AS naics4,
               collect(DISTINCT o.soc_code) AS llm_socs
        """, r=region,
    ).data()

    # Per-SOC employer pools at each threshold + LLM-curated.
    counts_at = {t: defaultdict(set) for t in THRESHOLDS}
    counts_naics_any = defaultdict(set)
    counts_llm = defaultdict(set)
    for emp in employers:
        oes = oes_socs_for_naics4(emp["naics4"])
        for r in oes:
            soc = r["soc"]
            if soc not in supported_socs:
                continue
            pct = r.get("pct_total") or 0.0
            counts_naics_any[soc].add(emp["name"])
            for t in THRESHOLDS:
                if pct >= t:
                    counts_at[t][soc].add(emp["name"])
        for soc in emp["llm_socs"]:
            if soc in supported_socs:
                counts_llm[soc].add(emp["name"])

    served_naics_any = {s for s, e in counts_naics_any.items() if e}
    served_llm = {s for s, e in counts_llm.items() if e}
    served_at = {t: {s for s, e in counts_at[t].items() if e} for t in THRESHOLDS}

    # Per-band breakdown.
    band_supported: dict[str, set[str]] = defaultdict(set)
    for soc in supported_socs:
        band_supported[_band(edu_by_soc.get(soc, ""))].add(soc)

    return {
        "college": college,
        "region": region,
        "n_employers": len(employers),
        "supported_socs": set(supported_socs),
        "supported_titles": supported_socs,
        "band_supported": dict(band_supported),
        "served_naics_any": served_naics_any,
        "served_llm": served_llm,
        "served_at": served_at,
        "counts_at": {t: {k: len(v) for k, v in counts_at[t].items()} for t in THRESHOLDS},
        "counts_llm": {k: len(v) for k, v in counts_llm.items()},
    }


def main(out_path: str) -> None:
    edu_by_soc = _load_education_for_socs()
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        colleges = [r["n"] for r in session.run(
            "MATCH (c:College) RETURN c.name AS n ORDER BY n"
        ).data()]
        results = [analyze_college(session, c, edu_by_soc) for c in colleges]
    driver.close()

    out: list[str] = []
    out.append("# Per-College Coverage: NAICS-matrix + pct_total filter\n\n")
    out.append(
        "Tests the proposition that a pct_total ≥ 1% filter on the "
        "NAICS-matrix employer-occupation linkage produces a "
        "partnership-candidate pool that is both comprehensive (vs. "
        "LLM-curation losing CTE signal) and defensible (vs. unfiltered "
        "NAICS lighting up every regional employer).\n\n"
    )
    out.append(
        "Method: per college, compute the set of supported SOCs "
        "(reachable via PREPARES_FOR from any course at the college), "
        "then for each SOC count distinct regional employers under five "
        "linkage rules — LLM-curated, NAICS-matrix unfiltered, and the "
        "NAICS-matrix at four pct_total thresholds (0.5%, 1%, 2%, 5%).\n\n"
    )

    out.append("## Headline coverage: SOCs with ≥1 candidate\n\n")
    out.append(
        "| College | Region | Supp. | LLM | NAICS | ≥0.5% | ≥1% | ≥2% | ≥5% |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    for r in results:
        n = len(r["supported_socs"])
        out.append(
            f"| {r['college']} | {r['region']} | {n} | "
            f"{len(r['served_llm'])} | {len(r['served_naics_any'])} | "
            f"{len(r['served_at'][0.5])} | {len(r['served_at'][1.0])} | "
            f"{len(r['served_at'][2.0])} | {len(r['served_at'][5.0])} |\n"
        )

    out.append("\n## Coverage as % of supported SOCs\n\n")
    out.append("| College | LLM | ≥1% | Δ (≥1% vs LLM) |\n|---|---:|---:|---:|\n")
    for r in results:
        n = len(r["supported_socs"]) or 1
        llm_pct = 100 * len(r["served_llm"]) / n
        f1_pct = 100 * len(r["served_at"][1.0]) / n
        out.append(
            f"| {r['college']} | {llm_pct:.1f}% | {f1_pct:.1f}% | "
            f"+{f1_pct - llm_pct:.1f} pp |\n"
        )

    out.append("\n## Restricted to direct-CTE bands (Strong + Moderate)\n\n")
    out.append(
        "Same coverage metric but restricted to SOCs whose typical "
        "entry-level education is postsecondary nondegree, associate's, "
        "high-school + on-the-job, or no formal credential — the bands "
        "where CCC training is the direct path.\n\n"
    )
    out.append(
        "| College | Direct-CTE supp. | LLM | ≥1% | LLM % | ≥1% % |\n"
        "|---|---:|---:|---:|---:|---:|\n"
    )
    for r in results:
        direct = (r["band_supported"].get("Strong CTE", set()) |
                  r["band_supported"].get("Moderate CTE", set()))
        n = len(direct) or 1
        llm_n = len(r["served_llm"] & direct)
        f1_n = len(r["served_at"][1.0] & direct)
        out.append(
            f"| {r['college']} | {len(direct)} | {llm_n} | {f1_n} | "
            f"{100*llm_n/n:.1f}% | {100*f1_n/n:.1f}% |\n"
        )

    out.append("\n## Method complementarity (full supported set)\n\n")
    out.append(
        "How the LLM-curated and NAICS-matrix-≥1% sets overlap. "
        "`Both` = SOCs served by both methods. `LLM only` = SOCs with "
        "LLM-curated candidates that drop out at ≥1%. `≥1% only` = "
        "SOCs with no LLM-curated candidates that the filter recovers. "
        "The recovery delta is the proposition under test.\n\n"
    )
    out.append("| College | Both | LLM only | ≥1% only | Neither |\n"
               "|---|---:|---:|---:|---:|\n")
    for r in results:
        both = r["served_llm"] & r["served_at"][1.0]
        llm_only = r["served_llm"] - r["served_at"][1.0]
        f1_only = r["served_at"][1.0] - r["served_llm"]
        neither = r["supported_socs"] - r["served_llm"] - r["served_at"][1.0]
        out.append(
            f"| {r['college']} | {len(both)} | {len(llm_only)} | "
            f"{len(f1_only)} | {len(neither)} |\n"
        )

    out.append("\n## Per-SOC candidate count distribution at ≥1%\n\n")
    out.append(
        "Distribution of the candidate-pool size per supported SOC "
        "after the ≥1% filter. The shape tells us whether SOCs end up "
        "with practical lists (handfuls of candidates) or extreme tails "
        "(either zero or hundreds).\n\n"
    )
    out.append(
        "| College | 0 | 1-5 | 6-15 | 16-50 | 51-100 | 100+ |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
    )
    for r in results:
        buckets = {"0": 0, "1-5": 0, "6-15": 0, "16-50": 0, "51-100": 0, "100+": 0}
        for soc in r["supported_socs"]:
            n = r["counts_at"][1.0].get(soc, 0)
            if n == 0: buckets["0"] += 1
            elif n <= 5: buckets["1-5"] += 1
            elif n <= 15: buckets["6-15"] += 1
            elif n <= 50: buckets["16-50"] += 1
            elif n <= 100: buckets["51-100"] += 1
            else: buckets["100+"] += 1
        out.append(
            f"| {r['college']} | "
            f"{buckets['0']} | {buckets['1-5']} | {buckets['6-15']} | "
            f"{buckets['16-50']} | {buckets['51-100']} | {buckets['100+']} |\n"
        )

    # Recovery examples — what does the filter find that LLM missed?
    out.append("\n## Recovery sample: SOCs with NAICS-≥1% candidates that LLM missed\n\n")
    out.append(
        "For Foothill College only — first 25 SOCs that the filter "
        "surfaces as having partnership candidates but the LLM-curated "
        "view returns zero employers for. Tests whether the recovered "
        "signal is meaningfully CTE-relevant or noise.\n\n"
    )
    foothill = next(r for r in results if r["college"] == "Foothill College")
    recovered = sorted(foothill["served_at"][1.0] - foothill["served_llm"],
                       key=lambda s: -foothill["counts_at"][1.0].get(s, 0))
    out.append("| SOC | Title | ≥1% candidates | Education band |\n"
               "|---|---|---:|---|\n")
    for soc in recovered[:25]:
        title = foothill["supported_titles"].get(soc, "")
        band = _band(edu_by_soc.get(soc, ""))
        n = foothill["counts_at"][1.0].get(soc, 0)
        out.append(f"| `{soc}` | {title} | {n} | {band} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main("/app/coverage_threshold_sweep.md")
