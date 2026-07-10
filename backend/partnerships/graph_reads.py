"""Centralized Neo4j reads for the partnership/landscape query layer.

These are the recurring reads that were inlined — with divergent aliases — across
resolve.py, clusters.py, landscape_build.py, and landscape_programs.py. Each takes an OPEN
``session`` so the caller keeps owning the transaction/session lifecycle (the
round-trip count and read isolation are preserved, which keeps the landscape
output byte-identical). This module is the single source of truth for each read:
change the Cypher here, not in N call sites.

Scope (Occam): only reads that were genuinely duplicated 3+ times with the same
shape live here. The per-college alignment read (landscape_build.py), the program-award
*series* reads (landscape_build.py / landscape_programs.py), and the program-name read
(clusters.py, one site) stay with their callers — consolidating them would mean
flag-laden over-abstraction, not clarity.
"""

from __future__ import annotations

from typing import Sequence


def regional_demand(session, region: str, socs: Sequence[str]) -> dict[str, dict]:
    """COE-region demand for ``socs`` as ``{soc_code -> row}``.

    The ``(:Region {name})-[:DEMANDS]->(:Occupation)`` read, previously inlined
    ~5x with different aliases. Returns canonical row dicts with keys:
    ``soc_code, title, description, annual_openings, annual_wage, growth_rate,
    employment``. Callers read the keys they need; extra keys are harmless. The
    dict preserves query order (insertion order), matching the prior ``.data()``
    list order where a caller iterated rows.
    """
    if not socs:
        return {}
    rows = session.run(
        "MATCH (r:Region {name: $region})-[d:DEMANDS]->(o:Occupation) "
        "WHERE o.soc_code IN $socs "
        "RETURN o.soc_code AS soc_code, o.title AS title, "
        "o.description AS description, d.annual_openings AS annual_openings, "
        "d.annual_wage AS annual_wage, d.growth_rate AS growth_rate, "
        "d.employment AS employment",
        region=region, socs=list(socs),
    ).data()
    return {r["soc_code"]: r for r in rows}


def latest_academic_year(session) -> str | None:
    """``max(AcademicYear.year)`` — the latest reported award year, which defines
    "current supply" (latest-year completers). Previously inlined in resolve.py
    and landscape_programs.py, and hardcoded as a constant in clusters.py."""
    rec = session.run("MATCH (ay:AcademicYear) RETURN max(ay.year) AS y").single()
    return rec["y"] if rec else None


def program_awards(session, colleges: Sequence[str], tops: Sequence[str], year) -> list[dict]:
    """Latest-year completers per ``(top6, college)`` for the in-scope programs —
    the supply primitive. Rows: ``{top6, college, n}`` (n = summed awards > 0).

    This is the single source of truth for supply: both the cluster decomposition
    (clusters.py) and the L1 lens (lens.py) must read awards identically, or their
    supply numbers drift and the dashboard contradicts the report. Same shape as
    the read previously inlined in clusters.cluster_map."""
    if not colleges or not tops or not year:
        return []
    return session.run(
        "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear {year: $y}) "
        "WHERE p.college IN $c AND p.top6 IN $t AND coalesce(a.count, 0) > 0 "
        "RETURN p.top6 AS top6, p.college AS college, sum(coalesce(a.count, 0)) AS n",
        y=year, c=list(colleges), t=list(tops),
    ).data()


def program_names(session, tops: Sequence[str]) -> dict[str, str]:
    """``{top6 -> program name}`` for the given TOP6 codes (any college that runs
    it). Used to label feeder programs in the lens / cluster views."""
    if not tops:
        return {}
    return {r["t"]: r["n"] for r in session.run(
        "MATCH (p:Program) WHERE p.top6 IN $t "
        "RETURN DISTINCT p.top6 AS t, p.name AS n", t=list(tops),
    ).data()}


def program_award_series(session, colleges: Sequence[str], tops: Sequence[str]) -> list[dict]:
    """Per ``(college, top6, academic_year)`` award counts — the full supply
    series behind the report's award-trend table. Same read as
    svamp_programs.build_programs_landscape, centralized so the trend numbers in
    the report can't drift from the dashboard. Rows: ``{college, top6, year, awards}``."""
    if not colleges or not tops:
        return []
    return session.run(
        "MATCH (pr:Program)-[a:AWARDED]->(ay:AcademicYear) "
        "WHERE pr.college IN $c AND pr.top6 IN $t "
        "RETURN pr.college AS college, pr.top6 AS top6, ay.year AS year, "
        "toInteger(sum(coalesce(a.count, 0))) AS awards",
        c=list(colleges), t=list(tops),
    ).data()


def program_enrollment_series(session, colleges: Sequence[str], tops: Sequence[str]) -> list[dict]:
    """Per ``(college, top6, term)`` enrollment counts — the enrollment-trend
    series. Rows: ``{college, top6, term, count}`` (term e.g. "Fall 2025")."""
    if not colleges or not tops:
        return []
    return session.run(
        "MATCH (pr:Program)-[e:ENROLLED]->(t:Term) "
        "WHERE pr.college IN $c AND pr.top6 IN $t "
        "RETURN pr.college AS college, pr.top6 AS top6, t.term AS term, "
        "toInteger(sum(e.count)) AS count",
        c=list(colleges), t=list(tops),
    ).data()
