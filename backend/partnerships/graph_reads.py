"""Centralized Neo4j reads for the partnership/landscape query layer.

These are the recurring reads that were inlined — with divergent aliases — across
resolve.py, clusters.py, svamp.py, and svamp_programs.py. Each takes an OPEN
``session`` so the caller keeps owning the transaction/session lifecycle (the
round-trip count and read isolation are preserved, which keeps the landscape
output byte-identical). This module is the single source of truth for each read:
change the Cypher here, not in N call sites.

Scope (Occam): only reads that were genuinely duplicated 3+ times with the same
shape live here. The per-college alignment read (svamp.py), the program-award
*series* reads (svamp.py / svamp_programs.py), and the program-name read
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
    and svamp_programs.py, and hardcoded as a constant in clusters.py."""
    rec = session.run("MATCH (ay:AcademicYear) RETURN max(ay.year) AS y").single()
    return rec["y"] if rec else None
