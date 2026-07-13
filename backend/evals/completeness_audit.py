"""Award-data completeness audit — graph ``AWARDED`` vs COE's ``supply_by_top.csv``.

The graph's supply is DataMart award completions loaded from ``ontology/datamart/program_awards/``.
COE publishes the same completions (per award level, over 2020–2023) in ``supply_by_top.csv``.
Where the export is complete and the windows overlap, the two agree completion-for-completion
(e.g. De Anza machining 095630: graph 44,64,49 = the sum of COE's award-level rows). This audit
quantifies that agreement, so an incomplete DataMart export can't silently undercount supply.

It caught the two export defects (both since fixed in ``pipeline/datamart_export.py``): the
``award_type`` filter excluded locally-approved awards (graph was CO-approved-only, COE is All
Awards), and the ``floor`` skipped 2020-2021. After a complete re-export the per-year ratio
should be ~1.0 for the overlap years — this is the re-export's acceptance test.

Run against a FULL graph (the seed is a curated subset and won't reflect full-graph
completeness):

    NEO4J_URI=bolt://localhost:7699 NEO4J_USERNAME=neo4j NEO4J_PASSWORD=… \\
        python3.11 -m evals.completeness_audit
"""
import csv
from collections import defaultdict

from ontology.supply import _normalize_college, _DATA_DIR
from ontology.schema import get_driver

# COE's file holds 2020-2021 … 2022-2023; the graph now covers these too (post re-export).
OVERLAP_YEARS = ["2020-2021", "2021-2022", "2022-2023"]
TOL = 0.5   # completions are integers; ±0.5 absorbs COE's rounded 3-yr-avg cells


def _csv_completions() -> dict[tuple[str, str], dict[str, float]]:
    """(top6, college_norm) -> {year: total completions across award levels} from COE's file."""
    out: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with open(_DATA_DIR / "supply_by_top.csv", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 7:
                continue
            top = row[0].strip().strip('"').split(" - ", 1)[0].strip()
            col = _normalize_college(row[1].strip()).lower()
            for i, y in enumerate(OVERLAP_YEARS):
                try:
                    out[(top, col)][y] += float(row[3 + i]) if row[3 + i].strip() else 0.0
                except ValueError:
                    pass
    return out


def _graph_completions(driver) -> dict[tuple[str, str], dict[str, float]]:
    """(top6, college_norm) -> {year: AWARDED count} from the graph, over the overlap years."""
    out: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with driver.session() as s:
        for row in s.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear) WHERE ay.year IN $y "
            "RETURN p.college AS c, p.top6 AS t, ay.year AS y, "
            "toInteger(sum(coalesce(a.count,0))) AS n", y=OVERLAP_YEARS).data():
            out[(row["t"], _normalize_college(row["c"]).lower())][row["y"]] += row["n"]
    return out


def audit(driver) -> dict:
    """Compare graph vs COE over COE's published cells. Returns per-year totals + cell counts."""
    coe, graph = _csv_completions(), _graph_completions(driver)
    per_year = {y: {"graph": 0.0, "coe": 0.0} for y in OVERLAP_YEARS}
    match = under = over = 0
    for k, years in coe.items():
        g = graph.get(k, {})
        for y in OVERLAP_YEARS:
            cv, gv = years.get(y, 0.0), g.get(y, 0.0)
            per_year[y]["graph"] += gv
            per_year[y]["coe"] += cv
            if abs(cv - gv) < TOL:
                match += 1
            elif gv < cv:
                under += 1
            else:
                over += 1
    return {"cells": len(coe), "match": match, "under": under, "over": over, "per_year": per_year}


def main():
    st = audit(get_driver())
    print(f"COE universe: {st['cells']} (top6×college) cells over {OVERLAP_YEARS}")
    print(f"  match(±{TOL}): {st['match']}   graph-under-COE: {st['under']}   graph-over-COE: {st['over']}")
    print("  completions by year:")
    gt = ct = 0.0
    for y, v in st["per_year"].items():
        gt += v["graph"]; ct += v["coe"]
        ratio = v["graph"] / v["coe"] if v["coe"] else 0.0
        print(f"    {y}: graph {v['graph']:>9,.0f}   COE {v['coe']:>9,.0f}   ratio {ratio:.2f}")
    print(f"    ALL: graph {gt:,.0f}  COE {ct:,.0f}  ratio {gt / ct if ct else 0:.2f}")


if __name__ == "__main__":
    main()
