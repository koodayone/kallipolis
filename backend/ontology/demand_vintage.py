"""One vintage, everywhere: does every copy of the COE occupational demand data agree with
the bundled export?

The export (`occupational_demand_middle_skill.csv`) is copied at four levels — derived
files committed to git, the graph, the eval corpora, and figures people wrote into report
definitions and the skill — and a refresh that updates some of them leaves the product
quoting two editions at once. These checks read every level and compare it with the
export, by vintage where a copy states one and by value where it does not. They are
deterministic and cheap (3,140 rows), and they are what "did we update everything" means.

Run: `python scripts/check_demand_vintage.py [--graph]` (the graph check needs Neo4j).
The file-level checks also run under pytest (ontology/test_demand_vintage.py) so a stale
copy fails CI.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ontology.crosswalks import COE_DEMAND_PATH
from ontology.supply import coe_demand_columns

BACKEND = Path(__file__).resolve().parent.parent
OCCUPATIONS = BACKEND / "occupations" / "occupations.json"
OCCUPATIONS_META = BACKEND / "occupations" / "occupations.meta.json"
SECTOR_SOCS = BACKEND / "partnerships" / "data" / "sector_socs.csv"
SEED = BACKEND / "evals" / "seed.json.gz"
SURFACES = BACKEND / "evals" / "char_surfaces"
GOLDENS = BACKEND / "evals" / "goldens"
SAVED = BACKEND / "partnerships" / "saved_reports"
SKILL = BACKEND.parent / ".claude" / "skills" / "evaluate-program" / "SKILL.md"

#: The export's metric columns → the property names every derived copy uses.
METRICS = {"employment": "jobs", "annual_wage": "annual", "growth_rate": "change", "annual_openings": "openings"}


@dataclass
class Finding:
    check: str
    ok: bool
    detail: str


@dataclass
class Export:
    vintage: str
    rows: dict[tuple[str, str], dict]            # (region, soc) → {employment, annual_wage, growth_rate, annual_openings, title, education}
    socs: set[str] = field(default_factory=set)
    regions: set[str] = field(default_factory=set)


def load_export(path: Path = COE_DEMAND_PATH) -> Export:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = coe_demand_columns(reader.fieldnames or [])
        rows = {}
        for r in reader:
            key = (r[cols.region].strip(), r[cols.soc].strip())
            def num(c, cast):
                v = (r.get(c) or "").strip()
                return cast(float(v)) if v else None
            rows[key] = {"employment": num(cols.jobs, int), "annual_wage": num(cols.annual, int),
                         "growth_rate": num(cols.change, float), "annual_openings": num(cols.openings, int),
                         "title": r[cols.title].strip(), "education": r[cols.education].strip()}
    return Export(cols.vintage, rows, {s for _, s in rows}, {g for g, _ in rows})


def _close(a, b) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(b)))


def check_occupations_json(x: Export) -> list[Finding]:
    """The generated universe: its sidecar's vintage, and every value against the export."""
    out = []
    if OCCUPATIONS_META.exists():
        meta = json.loads(OCCUPATIONS_META.read_text())
        out.append(Finding("occupations.meta.json vintage", meta.get("vintage") == x.vintage,
                           f"{meta.get('vintage')!r} vs export {x.vintage!r}"))
    else:
        out.append(Finding("occupations.meta.json vintage", False, "sidecar missing — run python -m occupations.generate"))
    occs = json.loads(OCCUPATIONS.read_text())
    socs = {o["soc_code"] for o in occs}
    out.append(Finding("occupations.json universe", socs == x.socs,
                       f"{len(socs)} SOCs vs export {len(x.socs)}; missing {sorted(x.socs - socs)[:5]}, extra {sorted(socs - x.socs)[:5]}"))
    bad = 0
    for o in occs:
        for region, m in o["regions"].items():
            src = x.rows.get((region, o["soc_code"]))
            if src is None or any(not _close(m.get(k), src[k]) for k in METRICS):
                bad += 1
        src_title = next((x.rows[k]["title"] for k in x.rows if k[1] == o["soc_code"]), None)
        if src_title and o["title"] != src_title:
            bad += 1
    out.append(Finding("occupations.json values", bad == 0, f"{bad} (region, SOC) rows or titles differ from the export"))
    return out


def check_sector_socs(x: Export) -> list[Finding]:
    with SECTOR_SOCS.open() as f:
        socs = {r["soc"] for r in csv.DictReader(f)}
    return [Finding("sector_socs.csv universe", socs == x.socs, f"{len(socs)} SOCs vs export {len(x.socs)}")]


def check_eval_seed(x: Export) -> list[Finding]:
    """The CI graph fixture: its DEMANDS rows and occupation titles against the export."""
    seed = json.loads(gzip.decompress(SEED.read_bytes()))
    rows = seed["edges"].get("DEMANDS", [])
    bad = [r for r in rows if (r["f_region"], r["t_soc"]) not in x.rows
           or any(not _close(r["props"].get(k), x.rows[(r["f_region"], r["t_soc"])][k]) for k in METRICS)]
    titles = [n for n in seed["nodes"].get("Occupation", [])
              if any(k[1] == n["soc_code"] for k in x.rows) and n["title"] != next(x.rows[k]["title"] for k in x.rows if k[1] == n["soc_code"])]
    return [Finding("eval seed DEMANDS values", not bad, f"{len(bad)} of {len(rows)} rows differ — run python -m evals.extract_seed"),
            Finding("eval seed occupation titles", not titles, f"{len(titles)} titles differ")]


def check_characterization(x: Export) -> list[Finding]:
    """The characterization corpus embeds the vintage string verbatim (76 files today)."""
    stale = []
    for f in sorted(SURFACES.glob("*.json")):
        for m in re.finditer(r"COE occupational demand \\?u2014 (\d{4}) base-year employment, (\d{4})\\?u2013(\d{4}) projection|"
                             r"COE occupational demand — (\d{4}) base-year employment, (\d{4})–(\d{4}) projection", f.read_text()):
            lit = m.group(0).replace("\\u2014", "—").replace("\\u2013", "–")
            if lit != x.vintage:
                stale.append(f.name)
                break
    n = len(list(SURFACES.glob("*.json")))
    return [Finding("characterization surfaces vintage", not stale,
                    f"{len(stale)} of {n} files embed another vintage — run python -m evals.characterization_surfaces"),
            Finding("characterization goldens", True, f"{len(list(GOLDENS.glob('*.json')))} goldens carry values, not a vintage — regenerate with python -m evals.characterization after a reload")]


def _member_region(member: str) -> str:
    from ontology.regions import COLLEGE_COE_REGION
    from partnerships.members import _catalog
    for name, rec in _catalog().items():
        if rec["key"] == member:
            return COLLEGE_COE_REGION.get(name, "Bay")
    return "Bay"                                            # consortia (svamp) are Bay-region today


def check_authored_figures(x: Export) -> list[Finding]:
    """Openings figures people wrote into report definitions: each must equal the export's
    value for one of the def's occupations in the member's region, or their sum."""
    out = []
    for p in sorted(SAVED.glob("*.json")):
        d = json.loads(p.read_text())
        note = d.get("demand_note") or ""
        figs = [int(m.replace(",", "")) for m in re.findall(r"(\d[\d,]*) openings", note)]
        if not figs:
            continue
        region = _member_region(d["member"])
        vals = [x.rows[(region, s)]["annual_openings"] for s in d["socs"] if (region, s) in x.rows]
        allowed = set(v for v in vals if v is not None) | {sum(v for v in vals if v is not None)}
        stale = [f for f in figs if f not in allowed]
        out.append(Finding(f"{p.stem} demand_note", not stale,
                           f"quotes {figs}; export ({region}) allows {sorted(allowed)}" if stale else f"{figs} match the export ({region})"))
    return out


def check_skill_example(x: Export) -> list[Finding]:
    text = SKILL.read_text() if SKILL.exists() else ""
    stale = []
    for soc, fig in re.findall(r"\(SOC (\d{2}-\d{4})\) ha(?:s|ve) roughly ([\d,]+) openings", text):
        live = x.rows.get(("Bay", soc), {}).get("annual_openings")
        if live is not None and int(fig.replace(",", "")) != live:
            stale.append(f"{soc}: skill says {fig}, export {live}")
    return [Finding("evaluate-program skill worked example", not stale, "; ".join(stale) or "matches the export (Bay)")]


def check_graph(x: Export) -> list[Finding]:
    """The live graph: every DEMANDS edge's values and vintage against the export."""
    from ontology.schema import get_driver, close_driver
    driver = get_driver()
    try:
        with driver.session() as s:
            recs = s.run("MATCH (r:Region)-[d:DEMANDS]->(o:Occupation) RETURN r.name AS region, o.soc_code AS soc, "
                         "d.employment AS employment, d.annual_wage AS annual_wage, d.growth_rate AS growth_rate, "
                         "d.annual_openings AS annual_openings, d.vintage AS vintage").data()
            n_occ = s.run("MATCH (o:Occupation) RETURN count(o) AS n").single()["n"]
    finally:
        close_driver()
    bad = [r for r in recs if (r["region"], r["soc"]) not in x.rows
           or any(not _close(r[k], x.rows[(r["region"], r["soc"])][k]) for k in METRICS)]
    vintages = {r["vintage"] for r in recs}
    return [Finding("graph DEMANDS edges", len(recs) == len(x.rows) and not bad,
                    f"{len(recs)} edges vs export {len(x.rows)}; {len(bad)} differ in value"),
            Finding("graph DEMANDS vintage", vintages == {x.vintage}, f"edge vintages {sorted(map(str, vintages))} vs export {x.vintage!r}"),
            Finding("graph occupation universe", n_occ == len(x.socs), f"{n_occ} Occupation nodes vs export {len(x.socs)}")]


def run_checks(graph: bool = False) -> list[Finding]:
    x = load_export()
    out = [Finding("export vintage", True, x.vintage)]
    for fn in (check_occupations_json, check_sector_socs, check_eval_seed, check_characterization,
               check_authored_figures, check_skill_example):
        out += fn(x)
    if graph:
        out += check_graph(x)
    return out
