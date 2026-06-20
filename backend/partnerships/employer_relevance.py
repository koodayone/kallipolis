"""The one employer-relevance law.

An employer's relevance to an industry / occupational cluster is how prominently
its NAICS staffing pattern weights that industry's TARGET occupations — the sum
of the BLS OEWS employment shares (``HIRES_FOR.pct_total``, already materialized
on the graph for every employer-occupation edge) over the target SOCs.

    relevance(employer, target_socs) = Σ over s in target_socs of pct_total(employer.naics4, s)

This reads as "what fraction of this employer's (industry's) workforce sits in
the cluster's occupations" — breadth across a coherent occupational family is
relevance by design. The coarse ``swp_sectors`` industry tag is NOT consulted: an
employer is relevant exactly to the degree its staffing pattern concentrates on
the target SOCs, so a dental office surfaces for the dental cluster and a
restaurant does not (it has no — or negligible — staffing-pattern weight there).

This is the single source of truth, replacing three divergent implementations:
  - svamp_employers ranked by firm size + a coarse swp_sectors tag,
  - dossier read e.display_name (91% null) / e.naics_title (absent) and sorted by
    e.size_rank (19% present), producing null-name garbage,
  - opportunity computed the same share from the OES CSV at request time.
All now read the score from the edge; the score is the law above.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class RankedEmployer:
    """An employer scored against a set of target SOCs, ranked best-first."""
    name: str
    naics4: str | None
    relevance: float                  # Σ pct_total over the target SOCs
    soc_count: int                    # # of target SOCs this employer hires for
    soc_pct: dict[str, float]         # {soc -> pct_total} over the target SOCs
    size_rank: int = 0                # EDD size band; tiebreaker only, never primary
    # Geo / detail — populated only when with_geo=True (svamp_employers' map):
    county: str | None = None
    lat: float | None = None
    lng: float | None = None
    sector: str | None = None
    website: str | None = None
    description: str | None = None
    size_class: str | None = None     # EDD employee-count band (display only)


def rank_employers(
    session,
    *,
    region: str,
    target_socs: Sequence[str],
    require_website: bool = False,
    with_geo: bool = False,
) -> list[RankedEmployer]:
    """Regional employers ranked by staffing-pattern relevance to ``target_socs``.

    One read over ``(:Region {name})<-[:IN_MARKET]-(:Employer)-[:HIRES_FOR]->
    (:Occupation)`` aggregating Σ ``pct_total`` per employer over the target SOCs,
    sorted ``(-relevance, -soc_count, -size_rank, name)``. ``require_website``
    keeps only web-validated firms (the map's plottability gate); ``with_geo``
    pulls the county/coordinates/website/description the map needs.
    """
    if not target_socs:
        return []
    geo_cols = (
        ", e.county AS county, e.lat AS lat, e.lng AS lng, e.sector AS sector, "
        "e.website AS website, e.description AS description, e.size_class AS size_class"
        if with_geo else ""
    )
    website_filter = "AND e.website IS NOT NULL" if require_website else ""
    rows = session.run(
        f"""
        MATCH (r:Region {{name: $region}})<-[:IN_MARKET]-(e:Employer)
              -[h:HIRES_FOR]->(o:Occupation)
        WHERE o.soc_code IN $socs {website_filter}
        WITH e, sum(h.pct_total) AS relevance, count(DISTINCT o) AS soc_count,
             collect({{soc: o.soc_code, pct: h.pct_total}}) AS pairs
        RETURN e.name AS name, e.naics4 AS naics4, relevance, soc_count, pairs,
               coalesce(e.size_rank, 0) AS size_rank{geo_cols}
        """,
        region=region, socs=list(target_socs),
    ).data()
    out = [
        RankedEmployer(
            name=r["name"], naics4=r.get("naics4"),
            relevance=r["relevance"] or 0.0, soc_count=r["soc_count"],
            soc_pct={p["soc"]: p["pct"] for p in r["pairs"]},
            size_rank=r.get("size_rank") or 0,
            county=r.get("county"), lat=r.get("lat"), lng=r.get("lng"),
            sector=r.get("sector"), website=r.get("website"),
            description=r.get("description"), size_class=r.get("size_class"),
        )
        for r in rows
    ]
    out.sort(key=lambda e: (-e.relevance, -e.soc_count, -e.size_rank, e.name))
    return out
