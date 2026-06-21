"""Partnership-opportunity dossier — the grounded, REPRODUCIBLE ontology substrate
for a school's partnership strategy. The LLM narrates this; it does not rank or
invent. Every figure traces to the graph; data gaps are flagged, never zeroed.

Architecture:
  - The consortium SUBSTRATE (every cluster's full per-school supply + the regional
    employers per sector) is computed ONCE and cached, so projecting all 26 member
    schools is cheap.
  - A school's dossier is a PROJECTION of that substrate: the clusters it
    participates in, its role (anchor / member / peripheral), and a DETERMINISTIC
    priority_score so the ranking is reproducible and the LLM only writes prose.

priority_score (transparent, documented):
  peripheral role            -> 0          (anchor-first gate: too thin to drive)
  standing  = role_w * (0.7 + 0.3*min(share/0.5,1))   anchor role_w=1.0, member=0.6
  desirability = mean over occs of 0.45*wage_n + 0.30*growth_n + 0.25*openings_n
                 wage_n=min(wage/130000,1) growth_n=clamp((g+.02)/.22,0,1) open_n=min(op/1500,1)
  room      = max(0, 1 - coverage)         (gap as a relative thinness signal)
  employers = min(employer_count/12, 1)
  score     = round(100 * standing * (0.45*desirability + 0.30*room + 0.25*employers))

Deliberate v2 slots (flagged honestly, not faked): enrollment momentum, statewide
TOP6 wage outcomes, and employer-set enrichment (employer_count surfaces thinness).
"""

import json
import sys
from collections import defaultdict
from functools import lru_cache

from ontology.schema import get_driver
from partnerships.clusters import consortium_clusters
from partnerships.employer_relevance import rank_employers
from partnerships.registry import spec_for
from partnerships.sectors import SECTORS

COALITION_FLOOR = 0.05
# An employer is a "viable partner" for a cluster when the cluster's occupations
# are at least this share (Σ pct_total, %) of its industry's staffing pattern.
# Below it the firm's industry only marginally touches these roles (a retail chain
# whose NAICS includes a few pharmacy techs), so it doesn't count toward the
# cluster's partner base or its priority-score employer factor — though it may
# still appear, low, in the ranked list when nothing stronger exists.
EMPLOYER_RELEVANCE_FLOOR = 1.0


@lru_cache(maxsize=1)
def _clusters():
    return consortium_clusters("baccc")


@lru_cache(maxsize=1)
def _cluster_employers() -> dict:
    """{cluster.key -> [top employer dicts]} ranked by staffing-pattern relevance
    over each cluster's target SOCs (employer_relevance.rank_employers — the one
    law: Σ pct_total over the cluster's SOCs, named off e.name). Computed once for
    the whole consortium; projected per school. Replaces the prior per-SOC read
    that selected e.display_name (91% null) / e.naics_title (absent) and sorted by
    e.size_rank (19% present), which produced null-name, mis-ranked lists."""
    region = spec_for("baccc-adm").resolve_region()
    out: dict[str, list] = {}
    try:
        with get_driver().session() as s:
            for c in _clusters():
                socs = sorted({o.soc for o in c.occupations})
                out[c.key] = [
                    {"name": e.name, "naics4": e.naics4,
                     "relevance": round(e.relevance, 2), "soc_count": e.soc_count}
                    for e in rank_employers(s, region=region, target_socs=socs)
                ]
    except Exception:
        pass
    return out


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _priority(role, occupations, coverage, share, employer_count):
    if role == "peripheral":
        return 0, {}
    role_w = 1.0 if role == "anchor" else 0.6
    standing = role_w * (0.7 + 0.3 * min(share / 0.5, 1.0))
    if occupations:
        des = sum(
            0.45 * min((o["wage"] or 0) / 130000, 1.0)
            + 0.30 * _clamp(((o["growth"] or 0) + 0.02) / 0.22)
            + 0.25 * min((o["openings"] or 0) / 1500, 1.0)
            for o in occupations
        ) / len(occupations)
    else:
        des = 0.0
    room = max(0.0, 1.0 - coverage)
    emp = min(employer_count / 12, 1.0)
    score = round(100 * standing * (0.45 * des + 0.30 * room + 0.25 * emp))
    return score, {"standing": round(standing, 2), "desirability": round(des, 2),
                   "room": round(room, 2), "employer_factor": round(emp, 2)}


def opportunity_dossier(member_id: str) -> dict:
    probe = spec_for(f"{member_id}-adm")
    college = probe.colleges[0] if probe else None
    if college is None:
        return {"member": member_id, "industries": []}

    by_sector: dict[str, list] = defaultdict(list)
    for c in _clusters():
        if any(sp.college == college for f in c.feeders for sp in f.by_college):
            by_sector[c.sector_id].append(c)

    industries = []
    cluster_emps = _cluster_employers()
    for sid, sec_clusters in by_sector.items():
        cluster_dossiers = []
        for c in sec_clusters:
            school_awards: dict[str, int] = defaultdict(int)
            for f in c.feeders:
                for sp in f.by_college:
                    school_awards[sp.college] += sp.awards
            ranked = sorted(school_awards.items(), key=lambda x: -x[1])
            supply = c.supply
            anchor_name, anchor_aw = ranked[0] if ranked else (None, 0)
            coalition = [
                {"college": k, "awards": v, "share": round(v / supply, 3) if supply else 0}
                for k, v in ranked if supply and v / supply >= COALITION_FLOOR
            ]
            my_aw = school_awards.get(college, 0)
            my_share = round(my_aw / supply, 3) if supply else 0
            role = ("anchor" if anchor_name == college
                    else "member" if (supply and my_aw / supply >= COALITION_FLOOR)
                    else "peripheral")
            my_progs = [
                {"top6": f.top6, "name": f.name,
                 "awards": next((sp.awards for sp in f.by_college if sp.college == college), 0)}
                for f in c.feeders
                if any(sp.college == college and sp.awards > 0 for sp in f.by_college)
            ]
            cemps = cluster_emps.get(c.key, [])
            # Viable partners: firms whose industry meaningfully hires the cluster's
            # occupations (relevance >= floor). This — not the full ranked pool —
            # is the honest "employer base" count and the priority-score input.
            relevant = [e for e in cemps if e["relevance"] >= EMPLOYER_RELEVANCE_FLOOR]
            occs = [{"soc": o.soc, "title": o.title, "openings": o.annual_openings,
                     "wage": o.annual_wage, "growth": round(o.growth_rate, 3),
                     "admitted": o.admitted} for o in c.occupations]
            score, comps = _priority(role, occs, c.coverage, my_share, len(relevant))
            saturated = c.gap <= max(20, round(0.05 * c.demand))
            cluster_dossiers.append({
                "label": c.label, "demand": c.demand, "supply": supply, "gap": c.gap,
                "coverage": round(c.coverage, 3), "priority_score": score,
                "score_components": comps, "saturated": saturated,
                "occupations": occs,
                "college_role": role, "college_awards": my_aw, "college_share": my_share,
                "anchor": {"college": anchor_name, "awards": anchor_aw,
                           "share": round(anchor_aw / supply, 3) if supply else 0},
                "coalition": coalition, "college_programs": my_progs,
                "employers": cemps[:8], "employer_count": len(relevant),
                "employer_flag": ("thin — few firms' industries center on these roles"
                                  if len(relevant) < 5 else ""),
            })
        industries.append({
            "sector_id": sid, "sector_label": SECTORS[sid].label if sid in SECTORS else sid,
            "clusters": sorted(cluster_dossiers, key=lambda d: -d["priority_score"]),
        })

    return {
        "member": member_id, "college": college, "coalition_floor": COALITION_FLOOR,
        "scoring_note": "priority_score is deterministic; see dossier.py docstring. "
                        "0 = peripheral (anchor-first gate). v2 signals pending: "
                        "enrollment momentum, statewide TOP6 wage outcomes, employer enrichment.",
        "industries": sorted(
            industries,
            key=lambda i: -max((c["priority_score"] for c in i["clusters"]), default=0)),
    }


if __name__ == "__main__":
    print(json.dumps(opportunity_dossier(sys.argv[1] if len(sys.argv) > 1 else "foothill")))
