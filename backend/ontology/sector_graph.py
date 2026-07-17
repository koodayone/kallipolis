"""Materialize the sector / crosswalk / composition ontology into the graph (Step 3a).

The engine's ontology — sector membership, the TOP->SOC crosswalk, and each member's authored composition —
lives today in Python (partnerships.sectors, ontology.crosswalks) + the registered specs. This loader
MIRRORS it into the graph as nodes/edges so a later step (3b) can read it there instead of running the
Python. It is ADDITIVE and idempotent (MERGE): it creates the ontology layer without touching the
demand/awards/enrollment facts and without changing any read path, so numbers stay unchanged. ``reconcile``
proves the graph matches the code — the gate that makes the 3b read-swap safe.

Edge names are collision-free: ``PREPARES_FOR`` (Course->Occupation), ``CONTAINS`` (Department->Course) and
``OFFERS`` (College->Course) are already taken by the course layer, so this ontology uses **COVERS**
(Sector->Occupation), **SCOPES** (Sector->ProgramFamily) and **CROSSWALKS_TO** (ProgramFamily->Occupation).

Boundary (see research/architecture/UNIFIED-ENGINE-PLAN.md, Step 3):
  - git-authoritative, materialized READ-ONLY here: Sector, ProgramFamily(vocational, home_sector),
    CROSSWALKS_TO (crosswalk), Sector-COVERS->Occupation, Sector-SCOPES->ProgramFamily. ``home_sector``
    is the DataVista/PCAH HOME classification (which sector a family *belongs to*, CCCCO-authoritative,
    1:1) — the classification layer, distinct from the SCOPES feeder set (which sector's occupations a
    family *supplies*, crosswalk-derived). The two genuinely differ (a program feeds occupations across
    sectors); keeping both, named, is deliberate.
  - graph-authoritative LATER (3c, with the authoring UI): the Composition INCLUDES/EXCLUDES — bootstrapped
    from the registered specs here so the model is complete and reconcilable today.
"""
from __future__ import annotations

from ontology.crosswalks import (
    _load_pcah_cte_top6,
    _load_top_to_cip,
    _load_vocational_top6,
    load_top_titles,
    top6_to_soc,
)
from ontology.schema import get_driver
from partnerships.landscape import routable_specs
from partnerships.sectors import SECTORS


# The DataVista / PCAH "Industry Sector or Occupational Cluster" name → our Sector id. DataVista (CCCCO)
# is the authority for a program family's HOME sector (1:1). "global_trade" is a DataVista cluster we do
# not analyze — kept as a slug so every classified family still resolves to a home; families absent from
# the publication get home_sector = "unclassified".
_DATAVISTA_TO_SID: dict[str, str] = {
    "Advanced Manufacturing": "adm",
    "Advanced Transportation and Logistics": "atl",
    "Agriculture, Water and Environmental Technologies": "agwet",
    "Business and Entrepreneurship": "business",
    "Education and Human Development": "edhd",
    "Energy, Construction and Utilities": "ecu",
    "Global Trade": "global_trade",
    "Health": "health",
    "Information and Communication Technologies - Digital Media": "ict",
    "Life Sciences - Biotechnology": "biotech",
    "Public Safety": "public_safety",
    "Retail, Hospitality and Tourism": "retail",
    "Unassigned": "unassigned",
}


def home_sector_by_top6() -> dict[str, str]:
    """{TOP6 → our Sector id} — a program family's authoritative HOME sector, from the DataVista (CCCCO
    PCAH) "TOP Codes to Sectors" publication. This is the classification layer: which sector a program
    *belongs to*, distinct from the crosswalk feeder set (which sector's occupations it *supplies*).
    Reuses the existing ``_load_pcah_cte_top6`` reader; every DataVista cluster maps to a sid."""
    return {t: _DATAVISTA_TO_SID[name] for t, name in _load_pcah_cte_top6().items()
            if name in _DATAVISTA_TO_SID}


def sector_scopes(sid: str) -> set[str]:
    """The sector's program membership = ``vocational`` families that cross-walk to one of the sector's
    occupations, minus the sector's crosswalk-noise (``excluded_tops``), minus the home-division gate.
    Member- and awards-independent — the canonical sector boundary that ``in_scope`` + ``relevant_tops``
    derive per request today. This is the one place the SCOPES edge-set is defined; 3b reads it from the graph."""
    sec = SECTORS[sid]
    socs = set(sec.socs)
    hd = sec.home_divisions
    reach = {t for t, ss in top6_to_soc(list(_load_vocational_top6())).items() if ss & socs}
    return {t for t in reach if t not in sec.excluded_tops and (not hd or t[:2] in hd)}


def load(driver=None) -> dict:
    """Idempotent materialization. Returns per-type counts. Safe to re-run."""
    driver = driver or get_driver()
    titles = load_top_titles()
    voc = _load_vocational_top6()
    home = home_sector_by_top6()                           # {top6 -> our Sector id} (DataVista HOME classification)
    xwalk = top6_to_soc(list(_load_top_to_cip()))          # {top6 -> {soc}}, the faithful crosswalk

    with driver.session() as s:
        s.run("UNWIND $rows AS r MERGE (x:Sector {id: r.id}) SET x.label = r.label, x.swp_tag = r.swp_tag",
              rows=[{"id": sid, "label": sec.label, "swp_tag": sec.swp_tag} for sid, sec in SECTORS.items()])
        s.run("UNWIND $rows AS r MERGE (pf:ProgramFamily {top6: r.top6}) "
              "SET pf.title = r.title, pf.vocational = r.voc, pf.home_sector = r.home",
              rows=[{"top6": t, "title": titles.get(t, ""), "voc": t in voc,
                     "home": home.get(t, "unclassified")} for t in titles])
        # Each college's Program instance links to its family.
        s.run("MATCH (p:Program) MATCH (pf:ProgramFamily {top6: p.top6}) MERGE (p)-[:INSTANCE_OF]->(pf)")
        # The crosswalk (only where the Occupation node exists — demand-less occ nodes arrive in 3b).
        s.run("UNWIND $rows AS r MATCH (pf:ProgramFamily {top6: r.top6}), (o:Occupation {soc_code: r.soc}) "
              "MERGE (pf)-[:CROSSWALKS_TO]->(o)",
              rows=[{"top6": t, "soc": soc} for t, socs in xwalk.items() for soc in socs])
        # Sector occupation membership.
        s.run("UNWIND $rows AS r MATCH (x:Sector {id: r.sid}), (o:Occupation {soc_code: r.soc}) "
              "MERGE (x)-[:COVERS]->(o)",
              rows=[{"sid": sid, "soc": soc} for sid, sec in SECTORS.items() for soc in sec.socs])
        # Sector program membership (the noise-corrected boundary).
        s.run("UNWIND $rows AS r MATCH (x:Sector {id: r.sid}), (pf:ProgramFamily {top6: r.top6}) "
              "MERGE (x)-[:SCOPES]->(pf)",
              rows=[{"sid": sid, "top6": t} for sid in SECTORS for t in sector_scopes(sid)])
        # Compositions — one node per AUTHORED instance, bootstrapped from the spec (SVAMP today).
        for spec in routable_specs():
            comp = spec.composition
            if not comp.is_authored and not comp.program_excludes:
                continue
            s.run("MERGE (c:Composition {id: $id}) SET c.member = $member, c.sector = $sector",
                  id=spec.id, member=spec.id, sector=spec.sector)
            if comp.occupations is not None:
                s.run("MATCH (c:Composition {id: $id}) UNWIND $socs AS soc "
                      "MATCH (o:Occupation {soc_code: soc}) MERGE (c)-[:INCLUDES]->(o)",
                      id=spec.id, socs=list(comp.occupations))
            if comp.program_excludes:
                s.run("MATCH (c:Composition {id: $id}) UNWIND $tops AS t "
                      "MATCH (pf:ProgramFamily {top6: t}) MERGE (c)-[:EXCLUDES]->(pf)",
                      id=spec.id, tops=list(comp.program_excludes))

    return counts(driver)


def counts(driver=None) -> dict:
    driver = driver or get_driver()
    with driver.session() as s:
        q = lambda c: s.run(c).single()[0]
        return {
            "Sector": q("MATCH (:Sector) RETURN count(*)"),
            "ProgramFamily": q("MATCH (:ProgramFamily) RETURN count(*)"),
            "CROSSWALKS_TO": q("MATCH (:ProgramFamily)-[:CROSSWALKS_TO]->() RETURN count(*)"),
            "COVERS": q("MATCH (:Sector)-[:COVERS]->() RETURN count(*)"),
            "SCOPES": q("MATCH (:Sector)-[:SCOPES]->() RETURN count(*)"),
            "home_sector": q("MATCH (pf:ProgramFamily) WHERE pf.home_sector <> 'unclassified' RETURN count(*)"),
            "Composition": q("MATCH (:Composition) RETURN count(*)"),
        }


def reconcile(driver=None) -> list[str]:
    """Assert the graph ontology reproduces the code, returning a list of discrepancies (empty = faithful).
    COVERS/CROSSWALKS_TO compare against the code sets INTERSECTED with occupations that have a node — the
    demand-less remainder is reported separately as ``pending_hollow`` (created in 3b), not a discrepancy."""
    driver = driver or get_driver()
    diffs: list[str] = []
    with driver.session() as s:
        have_occ = {r["x"] for r in s.run("MATCH (o:Occupation) RETURN o.soc_code AS x")}
        pending = 0
        for sid, sec in SECTORS.items():
            want = set(sec.socs) & have_occ
            got = {r["x"] for r in s.run(
                "MATCH (:Sector {id: $sid})-[:COVERS]->(o) RETURN o.soc_code AS x", sid=sid)}
            if want != got:
                diffs.append(f"COVERS[{sid}]: graph-code = {sorted(got - want)}, code-graph = {sorted(want - got)}")
            pending += len(set(sec.socs) - have_occ)
            want_sc = sector_scopes(sid)
            got_sc = {r["x"] for r in s.run(
                "MATCH (:Sector {id: $sid})-[:SCOPES]->(pf) RETURN pf.top6 AS x", sid=sid)}
            if want_sc != got_sc:
                diffs.append(f"SCOPES[{sid}]: graph-code = {sorted(got_sc - want_sc)}, code-graph = {sorted(want_sc - got_sc)}")
        xwalk = top6_to_soc(list(_load_top_to_cip()))
        want_pf = {(t, soc) for t, socs in xwalk.items() for soc in socs if soc in have_occ}
        got_pf = {(r["t"], r["s"]) for r in s.run(
            "MATCH (pf:ProgramFamily)-[:CROSSWALKS_TO]->(o) RETURN pf.top6 AS t, o.soc_code AS s")}
        if want_pf != got_pf:
            diffs.append(f"CROSSWALKS_TO: {len(got_pf - want_pf)} extra / {len(want_pf - got_pf)} missing edges")
        have_pf = {r["t"] for r in s.run("MATCH (pf:ProgramFamily) RETURN pf.top6 AS t")}
        want_home = {t: sid for t, sid in home_sector_by_top6().items() if t in have_pf}
        got_home = {r["t"]: r["h"] for r in s.run(
            "MATCH (pf:ProgramFamily) WHERE pf.home_sector <> 'unclassified' RETURN pf.top6 AS t, pf.home_sector AS h")}
        if want_home != got_home:
            mism = sorted(t for t in set(want_home) | set(got_home) if want_home.get(t) != got_home.get(t))
            diffs.append(f"home_sector: {len(mism)} families differ, e.g. {mism[:5]}")
        for spec in routable_specs():
            comp = spec.composition
            if comp.occupations is not None:
                got_inc = {r["x"] for r in s.run(
                    "MATCH (:Composition {id: $id})-[:INCLUDES]->(o) RETURN o.soc_code AS x", id=spec.id)}
                want_inc = set(comp.occupations) & have_occ
                if want_inc != got_inc:
                    diffs.append(f"INCLUDES[{spec.id}]: {sorted(got_inc ^ want_inc)}")
            if comp.program_excludes:
                got_exc = {r["x"] for r in s.run(
                    "MATCH (:Composition {id: $id})-[:EXCLUDES]->(pf) RETURN pf.top6 AS x", id=spec.id)}
                if set(comp.program_excludes) != got_exc:
                    diffs.append(f"EXCLUDES[{spec.id}]: {sorted(set(comp.program_excludes) ^ got_exc)}")
    if pending:
        diffs.append(f"pending_hollow: {pending} sector-occupation memberships await demand-less Occupation nodes (3b)")
    return diffs


if __name__ == "__main__":
    print("loaded:", load())
    d = reconcile()
    print("reconcile:", "FAITHFUL" if not d or all(x.startswith("pending_hollow") for x in d) else "DISCREPANCIES")
    for x in d:
        print("  -", x)
