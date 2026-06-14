"""Occupational-cluster decomposition of a resolved LandscapeSpec.

A *cluster* is a maximal set of the spec's resolved occupations linked by shared
training pipelines: two occupations are adjacent iff at least one in-scope TOP
program with latest-year awards feeds both (via the vocational crosswalk). A
cluster is a connected component of that graph.

Why connected components and not a similarity/threshold rule: because supply is
defined as "sum the awards of the programs feeding the cluster," the grouping must
guarantee every feeder program lands wholly inside ONE cluster — otherwise a
program's completers would be split across clusters or double-counted. Connected
components is the unique partition with that property: if a TOP feeds two SOCs,
those SOCs are by construction in the same component, so

    sum(cluster.supply for cluster in clusters) == sum(all feeder-program awards)

exactly — no leakage, no double count. This is the level at which the noisy
TOP->SOC crosswalk fan-out stops corrupting the supply/demand gap.

Consequences worth stating:
  - Supply is a CLUSTER property, never an occupation property. Feeders are
    shared, so an individual occupation has no clean standalone supply number —
    which is the whole reason to cluster before computing a gap.
  - demand is occupation-additive (regional annual openings are disjoint per SOC),
    so a cluster's demand is just the sum over its members.
  - gap = demand - supply is a RELATIVE signal: demand is the whole region's
    openings while supply is only the consortium's completers, and not every
    completer enters the field nor is every opening CC-fillable. Read it as
    "where is consortium supply thin against regional demand," not as a literal
    worker shortage.

Clustering runs on the POST-resolution SOC set (resolve.resolve), so it organizes
exactly the occupations the sector rule admitted (including curated below-floor
INCLUDE_SOCS admissions) and never changes membership.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ontology.crosswalks import _load_top_to_cip, top6_to_soc
from ontology.schema import get_driver
from partnerships.landscape import LandscapeSpec
from partnerships.resolve import resolve
from partnerships.sectors import INCLUDE_SOCS

_LATEST = "2024-2025"

# Curated cluster merges — human overrides that force occupations into one cluster
# even when the connected-components rule keeps them apart (they share no feeder
# program). This is the "data proposes, human confirms" layer: the mechanism groups
# by shared training pipeline; a curator may judge two pipelines to be one career
# cluster. Supply stays an EXACT partition because two separate components have
# disjoint feeder sets by construction, so merging them double-counts no TOP. Each
# entry is a set of SOCs to join wherever they co-occur in a resolved sector.
#   - The Advanced Manufacturing core — 17-3023 Engineering Technologists, 51-4041
#     Machinists, 49-9041 Industrial Machinery Mechanics, 51-4121 Welders: four
#     distinct programs (Engineering Tech/Electronics, Machining, Industrial Systems,
#     Welding) but one career destination — how a student exploring "advanced
#     manufacturing" actually sees the field — so the consortium treats them as one
#     partnership cluster. This collapses adm to a single cluster: an intentional
#     curatorial choice trading intra-sector resolution for a sector-level pathway.
# Each entry pairs the SOCs to join with a curated label — the auto-label just
# concatenates feeder-program names, which reads poorly for a deliberate merge.
CLUSTER_MERGES: list[tuple[frozenset[str], str]] = [
    (frozenset({"17-3023", "51-4041", "49-9041", "51-4121"}),
     "Advanced Manufacturing Trades & Technicians"),
    # Advanced Transportation: Auto Service (49-3023) joins the collision (49-3021),
    # diesel-truck (49-3031) and heavy-equipment (49-3042) group — all SOC 49-30xx
    # vehicle/mobile-equipment repair, one career family, distinct programs
    # (Automotive Technology vs Collision Repair vs Diesel).
    (frozenset({"49-3021", "49-3031", "49-3042", "49-3023"}),
     "Automotive & Diesel Service Technicians"),
]


@dataclass
class ClusterOccupation:
    """An occupation in a cluster, carrying its (occupation-additive) demand
    attributes. Supply is intentionally absent — it lives on the cluster."""
    soc: str
    title: str
    annual_openings: int
    annual_wage: int
    growth_rate: float
    admitted: bool  # True if a curated below-floor INCLUDE_SOCS admission


@dataclass
class SchoolProgram:
    """One (member college, feeder program) supply tuple with its latest-year
    awards — the school×TOP detail behind a cluster's supply."""
    college: str
    awards: int


@dataclass
class FeederProgram:
    top6: str
    name: str
    awards: int                            # latest-year completers, all colleges
    colleges: int                          # distinct member colleges awarding it
    by_college: list[SchoolProgram] = field(default_factory=list)  # desc by awards


@dataclass
class OccupationCluster:
    label: str                       # provisional, from the top feeders by awards
    occupations: list[ClusterOccupation]
    feeders: list[FeederProgram]
    n_colleges: int                  # distinct member colleges feeding the cluster
    sector_id: str = ""              # set by consortium_clusters; "" for a lone spec

    @property
    def key(self) -> str:
        """Stable id across endpoints: sector + smallest member SOC. Deterministic
        because the component (and thus its min SOC) is fixed for a given spec."""
        socs = sorted(o.soc for o in self.occupations)
        return f"{self.sector_id or '_'}:{socs[0]}" if socs else (self.sector_id or "_")

    @property
    def demand(self) -> int:
        return sum(o.annual_openings for o in self.occupations)

    @property
    def supply(self) -> int:
        return sum(f.awards for f in self.feeders)

    @property
    def gap(self) -> int:
        return self.demand - self.supply

    @property
    def coverage(self) -> float:
        return self.supply / self.demand if self.demand else 0.0

    @property
    def wage_low(self) -> int:
        return min((o.annual_wage for o in self.occupations), default=0)

    @property
    def wage_high(self) -> int:
        return max((o.annual_wage for o in self.occupations), default=0)


def cluster_map(spec: LandscapeSpec) -> list[OccupationCluster]:
    """Connected-component occupational clusters for `spec`, sorted by gap desc.

    Each cluster's `feeders` carry the full school×TOP breakdown (`by_college`),
    so a supply-detail view is a reserialization — no second clustering pass.
    """
    rs = resolve(spec)
    socs = list(rs.socs)
    if not socs:
        return []
    cols = list(spec.colleges)
    in_scope = [t for t in _load_top_to_cip() if spec.in_scope(t)]
    region = spec.resolve_region()

    with get_driver().session() as session:
        demand = {r["c"]: r for r in session.run(
            "MATCH (rg:Region {name: $rg})-[d:DEMANDS]->(o:Occupation) "
            "WHERE o.soc_code IN $s "
            "RETURN o.soc_code AS c, o.title AS t, d.annual_openings AS op, "
            "d.annual_wage AS w, d.growth_rate AS g",
            rg=region, s=socs).data()}
        award_rows = session.run(
            "MATCH (p:Program)-[a:AWARDED]->(ay:AcademicYear {year: $y}) "
            "WHERE p.college IN $c AND p.top6 IN $t AND coalesce(a.count, 0) > 0 "
            "RETURN p.top6 AS top6, p.college AS college, sum(coalesce(a.count, 0)) AS n",
            y=_LATEST, c=cols, t=in_scope).data()
        names = {r["t"]: r["n"] for r in session.run(
            "MATCH (p:Program) WHERE p.top6 IN $t "
            "RETURN DISTINCT p.top6 AS t, p.name AS n", t=in_scope).data()}

    top_awards: dict[str, int] = defaultdict(int)
    top_colleges: dict[str, set[str]] = defaultdict(set)
    top_by_college: dict[str, list[SchoolProgram]] = defaultdict(list)
    for r in award_rows:
        top_awards[r["top6"]] += r["n"]
        top_colleges[r["top6"]].add(r["college"])
        top_by_college[r["top6"]].append(SchoolProgram(college=r["college"], awards=r["n"]))
    awarded = set(top_awards)

    # SOC -> the awarded in-scope TOPs that feed it (the cluster-graph edges).
    feeders_of = {
        soc: {t for t in awarded if soc in top6_to_soc([t]).get(t, set())}
        for soc in socs
    }

    # Union-find: connect SOCs sharing any feeder TOP.
    parent = {soc: soc for soc in socs}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    soc_by_top: dict[str, list[str]] = defaultdict(list)
    for soc in socs:
        for t in feeders_of[soc]:
            soc_by_top[t].append(soc)
    for members in soc_by_top.values():
        for other in members[1:]:
            parent[find(members[0])] = find(other)

    # Curated overrides: force-join occupations a human judged one pathway. Only
    # touches SOCs present in this resolved set; disjoint-component merges keep the
    # supply partition exact.
    for group, _label in CLUSTER_MERGES:
        present = [s for s in group if s in parent]
        for other in present[1:]:
            parent[find(present[0])] = find(other)

    components: dict[str, list[str]] = defaultdict(list)
    for soc in socs:
        components[find(soc)].append(soc)

    clusters: list[OccupationCluster] = []
    for members in components.values():
        occs = []
        for soc in members:
            d = demand.get(soc, {})
            occs.append(ClusterOccupation(
                soc=soc, title=d.get("t", soc),
                annual_openings=d.get("op") or 0,
                annual_wage=d.get("w") or 0,
                growth_rate=d.get("g") or 0.0,
                admitted=soc in INCLUDE_SOCS,
            ))
        tops: set[str] = set()
        for soc in members:
            tops |= feeders_of[soc]
        feeders = [FeederProgram(
            top6=t, name=names.get(t, t), awards=top_awards[t],
            colleges=len(top_colleges[t]),
            by_college=sorted(top_by_college[t], key=lambda sp: -sp.awards),
        ) for t in tops]
        feeders.sort(key=lambda f: -f.awards)
        n_colleges = len(set().union(*[top_colleges[t] for t in tops])) if tops else 0
        label = " / ".join(f.name for f in feeders[:3])
        member_set = set(members)
        for grp, curated in CLUSTER_MERGES:
            if grp <= member_set:
                label = curated
                break
        clusters.append(OccupationCluster(
            label=label,
            occupations=sorted(occs, key=lambda o: -o.annual_openings),
            feeders=feeders,
            n_colleges=n_colleges,
        ))
    return sorted(clusters, key=lambda c: -c.gap)


def cluster_expanded_spec(spec: LandscapeSpec, sector_id: str) -> LandscapeSpec:
    """Single-college lens → its cluster consortium.

    A one-college landscape instance (e.g. foothill-ecu) normally renders just that
    college over the occupations it alone feeds. This expands it to the consortium
    clusters the college belongs to in this sector: `colleges` becomes the pool of
    co-member schools and `socs` becomes the cluster occupations — so the SAME
    dashboard (parameter-blind builders) renders the school inside its partnership
    pool, more columns and the cluster's occupations, identical in structure to the
    consortium instances. The college keeps its identity/accent; it is simply one
    member of the pool. Returns the spec UNCHANGED if it isn't single-college or the
    college belongs to no cluster here (graceful fall back to the solo view).

    soc_rule is preserved, so resolve() re-applies over the pool (identity on the
    already-resolved cluster set) and the coverage semantics stay consistent with
    the consortium views. counties is cleared — the pool spans the region, so the
    employer map draws the whole COE region rather than the lone college's county.
    """
    import dataclasses

    from partnerships.registry import spec_for

    if len(spec.colleges) != 1:
        return spec
    college = spec.colleges[0]
    baccc = spec_for(f"baccc-{sector_id}")
    if baccc is None:
        return spec
    mine = [
        c for c in cluster_map(baccc)
        if any(sp.college == college for f in c.feeders for sp in f.by_college)
    ]
    if not mine:
        return spec
    colleges = tuple(sorted(
        {sp.college for c in mine for f in c.feeders for sp in f.by_college}))
    socs = tuple(sorted({o.soc for c in mine for o in c.occupations}))
    return dataclasses.replace(spec, colleges=colleges, socs=socs, counties=())


def consortium_clusters(member_id: str) -> list[OccupationCluster]:
    """Every cluster across all of a member's sectors, gap-sorted, each tagged
    with its `sector_id`. The whole-consortium connected-components map (e.g.
    member_id="baccc" → the Bay Area consortium across all PCAH sectors)."""
    from partnerships.registry import spec_for
    from partnerships.sectors import SECTORS

    out: list[OccupationCluster] = []
    for sector_id in SECTORS:
        spec = spec_for(f"{member_id}-{sector_id}")
        if spec is None:
            continue
        for cl in cluster_map(spec):
            cl.sector_id = sector_id
            out.append(cl)
    return sorted(out, key=lambda c: -c.gap)
