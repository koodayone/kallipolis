"""Program node loader — the first-class TOP6 program the schema lacked.

TOP6 is the unit SWP funds and reports on, but it was smeared across the graph
as a property (Course.top_code, Student.primary_top6) and a TOP4-derived
Department. This loader instantiates it: a per-college Program node keyed
(college, top6), mirroring Course's (code, college) compound key.

Measures are dimensioned time-series at DIFFERENT grains (term vs. year), so
they live ON EDGES to shared time-dimension nodes — mirroring DEMANDS-on-edge,
never flattened onto the Program node:

    (Department)-[:HAS_PROGRAM]->(Program {college, top6, name, top4, is_cte})
    (Program)-[:AWARDED  {count, award_type}]->(AcademicYear {year})
    (Program)-[:ENROLLED {count, credit_type}]->(Term {term})

AcademicYear / Term are shared across all programs (a handful of nodes),
uniquely indexed so MERGE is a seek, not a scan.

Wages carry NO college dimension in the DataMart export and per-college
cohorts would be small-n suppressed, so wages are modeled at the TOP6 grain as
read-time reference data (mirroring supply.py / get_coe_supply over
supply_by_top.csv) via `get_wage_outcomes`, NOT as per-college graph edges.
Display-only, never summed (medians are non-additive).

Data: DataMart MIS exports (Chancellor's Office), scoped to the five SVAMP
colleges, colocated with supply_by_top.csv in this directory — a pivoted awards
summary, a pivoted wages summary, one CREDIT course-section file per college
(5-year term series), and one NONCREDIT course-section file covering all five
colleges (noncredit_course_sections.csv — DataMart scopes noncredit out of the
credit export, so it is its own pull; deliberately named OUTSIDE the
course_sections_*.csv glob because its hierarchy is one level shallower).
They are pivoted/hierarchical: hierarchy is encoded by indentation across
leading columns, and TOP6 appears as a SUFFIX ("Name-NNNNNN") in awards/wages
and a PREFIX ("NNNNNN - Name") in the course-section leaves. Term sets differ
per college (quarter vs. semester calendars), so enrollment terms are the
union across colleges, not a fixed list.

Runs after Course/Department exist (depends on the TOP6 universe) and before
the partnership precompute.
"""
from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path

from neo4j import Driver

from ontology.crosswalks import is_cte_top6, load_top_titles, top_to_department_name
from ontology.supply import _NEO4J_TO_SUPPLY

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent
_AWARDS_CSV = _DATA_DIR / "program_awards_summary.csv"
# Per-college course-section exports (5-year term series). One file per
# college; the term set differs by calendar (De Anza/Foothill/Mission run
# quarters, Evergreen/Ohlone semesters), so enrollment terms are the union
# across colleges, not a fixed list. Each is pivoted with THREE columns per
# term (Sections Count, Sections FTES, Enrollment Count).
_COURSE_SECTION_CSVS = sorted(_DATA_DIR.glob("course_sections_*.csv"))
# Noncredit course sections: ONE file for all five colleges (DataMart's
# noncredit pull), with a 2-level hierarchy — College Total -> TOP6 leaf —
# because the whole file is a single credit family. Named outside the
# course_sections_*.csv glob so the 3-level credit parser never sees it.
_NONCREDIT_SECTIONS_CSV = _DATA_DIR / "noncredit_course_sections.csv"
# The credit-family value noncredit ENROLLED edges carry — matches the
# export's own column naming ("Non-Credit Sections Count").
NONCREDIT_TYPE = "Non-Credit"
_WAGES_CSV = _DATA_DIR / "wage_outcomes_summary.csv"

# Supply CSV short label ("Deanza") -> canonical Neo4j college name
# ("De Anza College"). Reuse supply.py's authoritative map, reversed; the
# DataMart exports use the same short labels.
_SUPPLY_TO_NEO4J = {v: k for k, v in _NEO4J_TO_SUPPLY.items()}

_TOP6_SUFFIX = re.compile(r"-(\d{6})\s*$")
_TOP6_PREFIX = re.compile(r"^\s*(\d{6})\s*-")
_YEAR_RANGE = re.compile(r"\d{4}-\d{4}")


def _top6_suffix(s: str) -> str | None:
    m = _TOP6_SUFFIX.search(s.strip())
    return m.group(1) if m else None


def _top6_prefix(s: str) -> str | None:
    m = _TOP6_PREFIX.match(s)
    return m.group(1) if m else None


def _name_from_suffix(s: str) -> str:
    return _TOP6_SUFFIX.sub("", s.strip()).strip()


def _name_from_prefix(s: str) -> str:
    return _TOP6_PREFIX.sub("", s, count=1).strip()


def _to_int(s: str) -> int | None:
    s = (s or "").replace("$", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return int(round(float(s)))
    except ValueError:
        return None


def _canon(label: str) -> str | None:
    """CSV college label -> canonical Neo4j name (None if unknown)."""
    return _SUPPLY_TO_NEO4J.get(label.strip())


# ── Parsers (pivoted/hierarchical exports, indentation state machines) ────


def parse_awards() -> list[dict]:
    """Leaf award rows -> {college, top6, name, award_type, count, year}, one
    record per reported year. The export is pivoted like the enrollment one:
    a column per 'Annual YYYY-YYYY' from index 3 onward (single- or multi-year),
    so we read the value across every year column rather than a lone cell."""
    with open(_AWARDS_CSV, newline="") as f:
        rows = list(csv.reader(f))
    years = [
        (m.group(0) if (m := _YEAR_RANGE.search(h)) else h.strip())
        for h in rows[0][3:]
    ]
    out: list[dict] = []
    college = award_type = None
    for row in rows[1:]:
        c0, c1, c2 = (row + ["", "", ""])[:3]
        cells = row[3:3 + len(years)] if len(row) > 3 else []
        if c0.strip().endswith("Total") and c0.strip():
            college = _canon(c0.strip()[:-len("Total")].strip())
            continue
        if c1.strip().endswith("Total") and c1.strip():
            award_type = re.sub(r"\s+Total$", "", c1.strip())
            continue
        if c2.strip() and college:
            top6 = _top6_suffix(c2)
            if not top6:
                continue
            name = _name_from_suffix(c2)
            for year, raw in zip(years, cells):
                cnt = _to_int(raw)
                if cnt is not None:
                    out.append({
                        "college": college, "top6": top6, "name": name,
                        "award_type": award_type or "Award", "count": cnt, "year": year,
                    })
    return out


def parse_course_sections() -> list[dict]:
    """Per-college course-section exports -> {college, top6, name, credit_type,
    term, count}, one record per (program, term) with a reported Enrollment
    Count. Each file is pivoted with three columns per term (Sections Count /
    Sections FTES / Enrollment Count); we read the Enrollment Count column,
    located by the metric label rather than by fixed stride. Term columns
    differ per file (calendars differ), so each file is read on its own terms.
    Same hierarchy as the awards/enrollment summaries: College Total -> credit-
    type Total -> TOP6-prefixed leaf ("NNNNNN - Name")."""
    out: list[dict] = []
    for path in _COURSE_SECTION_CSVS:
        with open(path, newline="") as f:
            rows = list(csv.reader(f))
        if len(rows) < 2:
            continue
        terms_row, metric_row = rows[0], rows[1]
        # (column index, term) for every "Enrollment Count" column.
        enroll_cols = [
            (i, terms_row[i].strip())
            for i in range(3, len(metric_row))
            if metric_row[i].strip() == "Enrollment Count"
            and i < len(terms_row) and terms_row[i].strip()
        ]
        college = credit_type = None
        for row in rows[2:]:
            c0, c1, c2 = (row + ["", "", ""])[:3]
            if c0.strip().endswith("Total") and c0.strip():
                college = _canon(c0.strip()[:-len("Total")].strip())
                continue
            if c1.strip().endswith("Total") and c1.strip():
                credit_type = re.sub(r"\s+Total$", "", c1.strip())
                continue
            if c2.strip() and college:
                top6 = _top6_prefix(c2)
                if not top6:
                    continue
                name = _name_from_prefix(c2)
                for ci, term in enroll_cols:
                    cnt = _to_int(row[ci]) if ci < len(row) else None
                    if cnt is not None:
                        out.append({
                            "college": college, "top6": top6, "name": name,
                            "credit_type": credit_type or "Credit",
                            "term": term, "count": cnt,
                        })
    return out


def parse_noncredit_sections() -> list[dict]:
    """Noncredit course-section export -> the same record shape as
    parse_course_sections, with credit_type fixed to NONCREDIT_TYPE.

    The twin of parse_course_sections for the noncredit pull's shallower
    shape: ALL five colleges in one file, and no credit-family tier (the file
    IS one family), so the TOP6 leaf sits in column 1 and term data starts at
    column 2 — College Total -> TOP6-prefixed leaf ("NNNNNN - Name").
    Enrollment Count columns are located by metric label, as in the credit
    parser. A missing file is an empty list, not an error (the noncredit pull
    is newer than the credit ones)."""
    if not _NONCREDIT_SECTIONS_CSV.exists():
        return []
    with open(_NONCREDIT_SECTIONS_CSV, newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return []
    terms_row, metric_row = rows[0], rows[1]
    enroll_cols = [
        (i, terms_row[i].strip())
        for i in range(2, len(metric_row))
        if metric_row[i].strip() == "Enrollment Count"
        and i < len(terms_row) and terms_row[i].strip()
    ]
    out: list[dict] = []
    college = None
    for row in rows[2:]:
        c0, c1 = (row + ["", ""])[:2]
        if c0.strip().endswith("Total") and c0.strip():
            college = _canon(c0.strip()[:-len("Total")].strip())
            continue
        if c1.strip() and college:
            top6 = _top6_prefix(c1)
            if not top6:
                continue
            name = _name_from_prefix(c1)
            for ci, term in enroll_cols:
                cnt = _to_int(row[ci]) if ci < len(row) else None
                if cnt is not None:
                    out.append({
                        "college": college, "top6": top6, "name": name,
                        "credit_type": NONCREDIT_TYPE,
                        "term": term, "count": cnt,
                    })
    return out


@lru_cache(maxsize=1)
def _wage_index() -> dict[str, list[dict]]:
    """TOP6 -> list of recipient-type wage records (read-time reference data).

    Wages have no college dimension; keyed by TOP6 only. Window comes from the
    'Award Years YYYY-YYYY to YYYY-YYYY' header band.
    """
    with open(_WAGES_CSV, newline="") as f:
        rows = list(csv.reader(f))
    window = ""
    if len(rows) > 0 and len(rows[0]) > 2:
        wm = _YEAR_RANGE.findall(rows[0][2])
        window = f"{wm[0]} to {wm[1]}" if len(wm) >= 2 else (rows[0][2].strip() or "")
    idx: dict[str, list[dict]] = {}
    cur_top6 = None
    for row in rows[2:]:
        c0, c1 = (row + ["", ""])[:2]
        vals = row[2:6] if len(row) > 2 else []
        if c0.strip():
            cur_top6 = _top6_suffix(c0)
            continue
        if c1.strip() and cur_top6:
            wb, w2, w5, n = (list(vals) + [""] * 4)[:4]
            idx.setdefault(cur_top6, []).append({
                "recipient_type": c1.strip(),
                "wage_before": _to_int(wb), "wage_after_2": _to_int(w2),
                "wage_after_5": _to_int(w5), "n": _to_int(n), "window": window,
            })
    return idx


def get_wage_outcomes(top6: str) -> list[dict]:
    """Pooled statewide award-cohort wage outcomes for a TOP6 program, by
    recipient type. Display-only; medians are non-additive — never summed.

    TODO (move wages into the ontology): this read-time CSV lookup is a
    deliberate steel-thread shortcut, not the desired end state. The long-term
    goal is for all program data — wages included — to live in the graph. The
    blocker is that the DataMart wage export has no college dimension, so the
    honest graph model is TOP6-grain, not the per-college Program grain. The
    migration path when we take it:
      1. Add a CohortWindow {start_yr, end_yr} dimension node (already specced).
      2. Either (a) introduce a shared TOP6-level node these edges hang off of
         (a real reification of the program-as-TOP6, which the eventual
         Department=TOP4 → Program=TOP6 reparent in graph-model.md would make
         natural), or (b) attach WAGE_OUTCOME {recipient_type, wages, n,
         scope:"pooled_top6"} from each member college's Program to the shared
         CohortWindow with an explicit pooled flag — accepting storage
         duplication but never traversing it from roll-up queries.
      Prefer (a); it also resolves the PREPARES_FOR-belongs-on-TOP6 question.
    Until then, wages stay here as reference data, mirroring supply.py."""
    return _wage_index().get(top6, [])


# ── Loader ────────────────────────────────────────────────────────────────


def load_programs(driver: Driver) -> dict:
    """Idempotent: MERGE Program nodes (union of awards∪enrollment keys) for
    colleges present in the graph, link HAS_PROGRAM to the TOP4 Department where
    it exists, and materialize AWARDED / ENROLLED measure edges to shared
    AcademicYear / Term dimension nodes. Wages stay out of the graph (see
    get_wage_outcomes)."""
    awards = parse_awards()
    enroll = parse_course_sections() + parse_noncredit_sections()

    with driver.session() as session:
        existing = {r["name"] for r in session.run(
            "MATCH (c:College) RETURN c.name AS name").data()}

    awards = [a for a in awards if a["college"] in existing]
    enroll = [e for e in enroll if e["college"] in existing]

    # Program universe = union of (college, top6). The program name comes from
    # the Chancellor's Office Taxonomy of Programs (the authority), NOT the
    # DataMart display column — that column is truncated to a fixed width
    # (e.g. "Industrial Systems Technology and Mainte"). Fall back to the CSV
    # name only for a TOP6 absent from the taxonomy.
    top_titles = load_top_titles()
    programs: dict[tuple[str, str], dict] = {}
    for rec in enroll + awards:
        key = (rec["college"], rec["top6"])
        if key not in programs:
            top4 = rec["top6"][:4]
            programs[key] = {
                "college": rec["college"], "top6": rec["top6"],
                "name": top_titles.get(rec["top6"]) or rec["name"],
                "top4": top4, "is_cte": is_cte_top6(rec["top6"]),
                "dept": top_to_department_name(rec["top6"]),
            }
    prog_rows = list(programs.values())

    with driver.session() as session:
        session.run(
            """
            UNWIND $rows AS p
            MERGE (pr:Program {college: p.college, top6: p.top6})
            SET pr.name = p.name, pr.top4 = p.top4, pr.is_cte = p.is_cte
            """, rows=prog_rows)
        # HAS_PROGRAM from the TOP4 Department where that Department exists.
        session.run(
            """
            UNWIND $rows AS p
            MATCH (pr:Program {college: p.college, top6: p.top6})
            MATCH (d:Department {name: p.dept})
            MERGE (d)-[:HAS_PROGRAM]->(pr)
            """, rows=[p for p in prog_rows if p["dept"]])
        # AWARDED -> shared AcademicYear (keyed by award_type on the edge).
        session.run(
            """
            UNWIND $rows AS a
            MATCH (pr:Program {college: a.college, top6: a.top6})
            MERGE (ay:AcademicYear {year: a.year})
            MERGE (pr)-[r:AWARDED {award_type: a.award_type}]->(ay)
            SET r.count = a.count
            """, rows=awards)
        # ENROLLED -> shared Term (keyed by credit_type on the edge).
        session.run(
            """
            UNWIND $rows AS e
            MATCH (pr:Program {college: e.college, top6: e.top6})
            MERGE (t:Term {term: e.term})
            MERGE (pr)-[r:ENROLLED {credit_type: e.credit_type}]->(t)
            SET r.count = e.count
            """, rows=enroll)

    stats = {
        "programs": len(prog_rows),
        "awarded_edges": len(awards),
        "enrolled_edges": len(enroll),
        "wage_top6": len(_wage_index()),
        "colleges": sorted({p["college"] for p in prog_rows}),
    }
    logger.info("load_programs: %s", stats)
    return stats
