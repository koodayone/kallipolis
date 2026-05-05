"""Emit a reviewable markdown report of Occupation → SWP sector assignments.

Classification is computed off the institutional crosswalk directly:
for each Occupation, collect every TOP6 that reaches its SOC via
TOP6→CIP→SOC, look up each TOP6's PCAH sector, and pick the plurality
sector. College-independent — the same answer regardless of which
colleges are loaded.
"""

from __future__ import annotations

import csv
import os
from collections import Counter
from pathlib import Path

import openpyxl
from neo4j import GraphDatabase

from ontology.crosswalks import (
    PCAH_SECTORS_PATH,
    TOP_CIP_PATH,
    _load_cip_to_soc,
    _load_pcah_cte_top6,
    _load_top_to_cip,
)


def _load_top6_titles() -> dict[str, str]:
    """Combine PCAH (CTE-only) and TOP-CIP (broader) into one TOP6 → title
    lookup. PCAH wins on overlap — it's the authoritative SWP source."""
    titles: dict[str, str] = {}
    with open(TOP_CIP_PATH, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            raw = row[0].strip().strip('"')
            if " - " not in raw:
                continue
            code_part, title_part = raw.split(" - ", 1)
            top6 = code_part.replace(".", "")
            if len(top6) == 6 and top6.isdigit():
                titles.setdefault(top6, title_part.strip())
    wb = openpyxl.load_workbook(PCAH_SECTORS_PATH, read_only=True)
    ws = wb["Sheet1"]
    for row in ws.iter_rows(min_row=3, values_only=True):
        top6_val, title, _sector = row
        if top6_val is None or title is None:
            continue
        titles[f"{int(top6_val):06d}"] = str(title)
    wb.close()
    return titles


def _build_soc_to_tops() -> dict[str, set[str]]:
    """Reverse the TOP6→CIP→SOC chain to {soc: {top6, ...}}."""
    top_cip = _load_top_to_cip()
    cip_soc = _load_cip_to_soc()
    soc_to_tops: dict[str, set[str]] = {}
    for top6, cips in top_cip.items():
        for cip in cips:
            for soc in cip_soc.get(cip, set()):
                soc_to_tops.setdefault(soc, set()).add(top6)
    return soc_to_tops


def _fmt_tops(tops: list[str], titles: dict[str, str]) -> str:
    return "; ".join(
        f"`{t}` {titles.get(t, '(no title)')}" for t in sorted(tops)
    )


def winner(d: Counter) -> list[str]:
    if not d:
        return []
    top = max(d.values())
    return sorted([s for s, c in d.items() if c == top])


def main(out_path: str) -> None:
    top6_to_sector = _load_pcah_cte_top6()
    top6_titles = _load_top6_titles()
    soc_to_tops = _build_soc_to_tops()

    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (occ:Occupation)
            RETURN occ.soc_code AS soc, occ.title AS title
            ORDER BY soc
            """
        ).data()
    driver.close()

    by_sector: dict[str, list[dict]] = {}
    ties: list[dict] = []
    untraceable: list[dict] = []
    no_crosswalk: list[tuple[str, str]] = []

    for r in rows:
        soc, title = r["soc"], r["title"]
        tops = sorted(soc_to_tops.get(soc, set()))
        if not tops:
            no_crosswalk.append((soc, title))
            continue

        votes: Counter = Counter()
        tops_by_sector: dict[str, list[str]] = {}
        cte_tops: list[str] = []
        non_cte_tops: list[str] = []
        for t in tops:
            sector = top6_to_sector.get(t)
            if sector is None:
                non_cte_tops.append(t)
                continue
            cte_tops.append(t)
            votes[sector] += 1
            tops_by_sector.setdefault(sector, []).append(t)

        if not votes:
            untraceable.append({"soc": soc, "title": title, "tops": tops})
            continue

        winners = winner(votes)
        record = {
            "soc": soc, "title": title,
            "votes": dict(votes),
            "tops_by_sector": tops_by_sector,
            "non_cte_tops": non_cte_tops,
            "winners": winners,
        }
        if len(winners) == 1:
            by_sector.setdefault(winners[0], []).append(record)
        else:
            ties.append(record)

    out: list[str] = []
    out.append("# Occupation → SWP Sector Classification\n")
    out.append(
        "Plurality classification of every `Occupation` in the graph to "
        "a Strong Workforce / Doing-What-MATTERS sector, computed off "
        "the institutional crosswalk directly. For each SOC, the full "
        "set of TOP6 codes that reach it via TOP6→CIP→SOC is collected; "
        "each TOP6's sector is looked up in the PCAH *TOP Codes to "
        "Sectors* file; the plurality sector wins.\n"
    )
    out.append(
        "**Method.** One vote per TOP6 in the crosswalk that reaches "
        "the SOC. College-independent — the result does not depend on "
        "which colleges are currently loaded into the graph. Inputs are "
        "exclusively the TOP-CIP (Chancellor's Office), CIP-SOC "
        "(NCES/BLS), and PCAH (Chancellor's Office) crosswalks shipped "
        "in `backend/ontology/data/`.\n"
    )
    out.append("**Inputs.**\n")
    out.append(f"- `Occupation` nodes: {len(rows)}\n")
    out.append(
        "- Crosswalks: `top_cip_crosswalk.csv`, "
        "`CIP2020_SOC2018_Crosswalk.xlsx`, `TOP Codes to Sectors.xlsx`\n"
    )

    classified = sum(len(v) for v in by_sector.values())
    out.append("\n## Coverage summary\n")
    out.append("| Bucket | Count | Pct |\n|---|---:|---:|\n")
    out.append(f"| Single-sector (clean plurality) | {classified} | "
               f"{100*classified/len(rows):.1f}% |\n")
    out.append(f"| Tied across two or more sectors | {len(ties)} | "
               f"{100*len(ties)/len(rows):.1f}% |\n")
    out.append(f"| Untraceable (TOPs exist but none in PCAH CTE set) | "
               f"{len(untraceable)} | {100*len(untraceable)/len(rows):.1f}% |\n")
    out.append(f"| No crosswalk path at all | {len(no_crosswalk)} | "
               f"{100*len(no_crosswalk)/len(rows):.1f}% |\n")

    out.append("\n## Sector totals (single-winner SOCs only)\n")
    out.append("| Sector | SOCs |\n|---|---:|\n")
    for sector, recs in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        out.append(f"| {sector} | {len(recs)} |\n")

    out.append("\n---\n")
    out.append("\n## Occupations by sector\n")
    out.append(
        "Each row shows the count of TOP6 codes voting for the winning "
        "sector vs the total CTE-classified TOPs that reach the SOC, "
        "and the contributing TOPs (with Chancellor's Office titles).\n"
    )
    for sector, recs in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        out.append(f"\n### {sector}  ({len(recs)} occupations)\n")
        out.append("| SOC | Title | Vote | Contributing TOPs |\n"
                   "|---|---|---|---|\n")
        for r in sorted(recs, key=lambda r: r["soc"]):
            this = r["votes"][sector]
            total = sum(r["votes"].values())
            tops = _fmt_tops(r["tops_by_sector"][sector], top6_titles)
            out.append(
                f"| `{r['soc']}` | {r['title']} | {this}/{total} | {tops} |\n"
            )

    out.append("\n---\n")
    out.append(f"\n## Tied occupations  ({len(ties)})\n")
    out.append(
        "These SOCs have no single-sector plurality — multiple sectors "
        "are tied for the top vote count. Each row shows the full "
        "sector breakdown with contributing TOPs.\n"
    )
    out.append("| SOC | Title | Sector breakdown |\n|---|---|---|\n")
    for r in sorted(ties, key=lambda r: (-len(r["votes"]), r["soc"])):
        chunks = []
        for s, c in sorted(r["votes"].items(), key=lambda x: -x[1]):
            tops = _fmt_tops(r["tops_by_sector"][s], top6_titles)
            chunks.append(f"**{s}** ({c}): {tops}")
        out.append(
            f"| `{r['soc']}` | {r['title']} | {'<br>'.join(chunks)} |\n"
        )

    out.append("\n---\n")
    out.append(f"\n## Untraceable occupations  ({len(untraceable)})\n")
    out.append(
        "These SOCs have TOPs in the crosswalk, but none of those TOPs "
        "appear in the PCAH CTE sector file — they would need either a "
        "non-CTE sector mapping or exclusion from the classification.\n"
    )
    if untraceable:
        out.append("| SOC | Title | TOP6 codes |\n|---|---|---|\n")
        for r in sorted(untraceable, key=lambda r: r["soc"]):
            tops = _fmt_tops(r["tops"], top6_titles)
            out.append(f"| `{r['soc']}` | {r['title']} | {tops} |\n")

    out.append("\n---\n")
    out.append(f"\n## SOCs with no crosswalk path  ({len(no_crosswalk)})\n")
    out.append(
        "These SOCs have no TOP6→CIP→SOC path at all in the institutional "
        "crosswalk. They cannot be classified by this method without an "
        "alternate route (e.g., the OEWS industry-occupation matrix).\n"
    )
    if no_crosswalk:
        out.append("| SOC | Title |\n|---|---|\n")
        for soc, title in sorted(no_crosswalk):
            out.append(f"| `{soc}` | {title} |\n")

    Path(out_path).write_text("".join(out))
    print(f"Wrote {out_path} ({len(rows)} occupations)")


if __name__ == "__main__":
    main("/app/sector_classification.md")
