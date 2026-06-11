# Member × Sector Gap Analysis — Architecture Plan

**Status: proposal / not yet implemented.** A working spec for scaling the aggregated-landscape engine (today: SVAMP + the 11 SMCCD sector views) into a system that produces a supply/demand gap analysis for every California community college, grounded in district- and consortium-level context, and queryable by an LLM through an MCP server. Lives in `backend/docs/` (not the audited `docs/` tree) because it describes unbuilt work; promote relevant sections into `docs/architecture/` as they ship.

---

## 1. Purpose (the telos)

This is **not a viewer**. The current dashboards display a member × sector landscape; the system this plan describes is a **supply/demand gap-analysis engine** whose output is a *strategic program- and partnership-development strategy for each individual school*, contextualized by what its district and consortium/region look like.

Three commitments fall out of that:

- **The gap is the analytical core**, not a display detail. Every view exists to answer: where does regional labor-market demand outrun this member's program supply, and what should they do about it?
- **The school is the unit of strategy**; the district and consortium/region are the *analytical context* that determines *where a gap lives* and therefore *how to act on it* (build a program locally vs. coordinate across a district vs. lead a consortium initiative).
- **The member hierarchy is the analytical frame**, not just a navigation convenience. Rolling supply up the `college ⊂ district ⊂ region` hierarchy and differencing against shared regional demand is exactly the gap computation.

This reframes the existing Occupation Coverage matrix (Covered / Partial / Gap) from a per-instance display widget into the primitive the whole system is built around.

## 1a. Hard constraint: no regression, URLs preserved

This is a **non-negotiable acceptance gate**, not a goal. The currently-live views — SVAMP, all 11 SMCCD sector views, and the per-college / State Atlas surfaces — must not functionally regress, and their URLs must be preserved byte-identical:

- **Frontend URLs preserved:** `/svamp`, `/svamp/report`, `/smccd` (→ `/smccd-adm`), every `/smccd-<sector>` and its `/report`, the `/[collegeId]/...` tree, and `/`.
- **Backend URLs preserved:** `/partnerships/svamp`, `/partnerships/smccd-<sector>`, and the `/employers`, `/programs`, `/program/{top6}`, `/occupation/{soc}` sub-routes. A dynamic `/partnerships/{id}` (§9) matches these paths identically — a param route is not a URL change.
- **Behavior preserved:** the numbers, coverage states, and employer sets these views render today are the regression baseline. The refactor is *behavior-preserving by construction*, proven by snapshots (Phase 0, §12), not by inspection.

The corollary for routing (§8): the existing flat landscape URLs are kept as-is. The scaling route is **additive** for new members; existing routes are not migrated. See §8 for the additive-vs-dispatcher trade-off.

## 2. The combinatorial space

Three axes; the member axis is a hierarchy, not a flat set.

- **Member** — `college ⊂ district ⊂ region ⊂ state`.
- **Sector** — 11 SWP vocational sectors (`partnerships/sectors.py`; `unassigned` / `non_cte_stem` excluded).
- **Surface / lens** — dashboard vs report; programs / occupations / employers within each.

Naive member × sector cardinality:

| member level | count | × 11 sectors |
|---|---|---|
| colleges | 115 | 1,265 |
| multi-college districts | ~24 | ~264 |
| COE regions | ~10 | ~110 |
| state | 1 | 11 |
| naive total | | **~1,650** |

Two prunings make the *real* space ~700–900:

- **Supply sparsity** — a (member, sector) is meaningful only if the member has a CTE program feeding that sector's SOCs. Computable, not guessed: `is_vocational` TOPs ∩ crosswalk-reachable(sector SOCs) ∩ the member's colleges. Each college has programs in ~4–8 of 11 sectors.
- **Single-college collapse** — ~49 of CA's 73 districts are single-college; their district view ≡ the college view. Only multi-college districts add a distinct aggregation.

This pruned set doubles as the **publish gate** (§7).

## 3. The load-bearing invariant, generalized

The engine rests on one rule (`partnerships/landscape.py`): **demand and employers are REGIONAL** (one number per region per SOC); **supply is INSTITUTIONAL** (summed across member colleges). Today `resolve_region()` *asserts the members collapse to exactly one COE region*.

Generalize to `resolve_regions()`: **read demand/employers per-region over the member's region set; sum supply over the member's colleges.** Single-region (college, and essentially all CA districts — they are geographically compact) is the `|regions| == 1` case. Region and state come for free. With members modeled in the graph (§5), "the member's colleges" and "the member's regions" are traversals, not lookups.

The one genuine edge: **statewide** spans all regions, so demand is a per-region union (openings sum to a state total; wages aggregate weighted), not a single number. That is the only place the current single-region assumption must actually bend, and it is out of scope for the school/district focus — but the generalized signature anticipates it.

## 4. The analytical model: gap as the core primitive

For a `(member, sector, occupation)` triple:

- **Demand** (regional) — annual openings, median wage, growth, after the BACCC "priority job" `SectorRule` (`partnerships/resolve.py::effective_socs`).
- **Supply** (institutional) — programs feeding the occupation via the crosswalk, with awards + enrollments, summed over the member's colleges.
- **Coverage** — the existing trichotomy: **Covered** (demand + producing supply), **Partial** (demand + thin/dormant supply), **Gap** (demand + no feeding program).

Two strategic opportunity types derive from coverage:

1. **Program-development opportunity** — high-demand occupation with a *Gap* or *Partial* at this member → build or strengthen a program.
2. **Partnership opportunity** — occupation the member *does* supply, with regional employers hiring for it but no relationship → the SWP "discover → propose → fund" flow.

**Multi-level localization is the strategic insight.** The same regional demand is the denominator at every level; the question is *at what level the supply gap closes*:

| Gap exists at | Diagnosis | Strategic response |
|---|---|---|
| school, but a sister college in the district serves it | local gap, district has a model | replicate / share the program (low cost) |
| whole district, but served elsewhere in the region | district-wide gap | benchmark + partner regionally |
| whole region (no college serves it despite demand) | greenfield regional gap | consortium-led new program (high value) |

So the recommendation engine = compute supply at each hierarchy level (the §6 roll-up), difference against regional demand, and route the response by the lowest level at which supply already exists. Prioritize by demand magnitude (openings × wage) × feasibility (does a near-peer already run it?) × strategic fit.

## 5. Graph as substrate — the MCP-readiness decision

The end goal includes an **MCP server queryable by Claude/ChatGPT**. That requirement is decisive: a flat-file member catalog is **invisible to Cypher**, so an LLM doing NL→Cypher (already present in the backend via `ANTHROPIC_API_KEY`) could not reason over members. Members must be graph-traversable.

This is not CSV *xor* graph — it is the repo's existing **source → manifestation** pattern (`sector_socs.csv`, `top_vocational.csv` are committed sources loaded into graph state):

```
members.csv  ──loader──►  (:District)-[:IN_REGION]->(:Region),  (:College)-[:IN_DISTRICT]->(:District)
(git-diffable source)      (Cypher-queryable manifestation)
```

Keeps the reviewable, diffable source *and* gets MCP-queryability. Caveat to resolve: `Region` nodes exist (~10 in the graph) but `COLLEGE_COE_REGION` (`backend/ontology/regions.py`) is **code, not edges** — for MCP, `College-[:IN_REGION]->Region` must be materialized as edges.

The deeper consequence: build the **projection layer** (`view(member, sector)`, `list_members()`, `compare(members, sector)`, `gaps(member)`) as **pure functions over the graph**. Three clients sit on it:

```
                  ┌─ REST API   → the atlas
graph ─► projection layer ─┼─ MCP tools  → Claude / ChatGPT (curated, reliable)
                  └─ NL→Cypher → open-ended LLM queries (already exists)
```

The MCP server is a **thin adapter exposing the same vetted assembly functions the atlas uses** — not a reimplementation. Offer both MCP layers: curated structured tools (= the projection functions, correct-by-construction) for common asks, and NL→Cypher for open-ended exploration. The structured layer is what keeps the LLM from hallucinating joins.

## 6. The aggregation algebra (precompute atoms, assemble views)

Today each landscape runs fresh graph queries (`partnerships/svamp.py::build_landscape`). The pieces are shared, so the system is an OLAP cube in disguise:

- **`demand(region, sector)`** — shared by every member in the region. ~10 × ~250 SOCs → tiny.
- **`employers(region, sector)`** — regional nodes; a member view filters by its county shed.
- **`supply(college, sector)`** — the institutional atom; ~700 sparse atoms.

Then any view is a pure assembly:

```
view(member, sector) = Σ supply(c, sector) for c in member.colleges
                       ⋈ demand(member.regions, sector)
                       ⋈ employers(member.regions, sector) filtered by member.counties
gap(member, sector)  = demand(member.regions, sector) − Σ supply(c, sector)
```

Member rolls up the hierarchy additively. The curation layer (`SectorRule`, `excluded_tops`) is sector-level and member-invariant — it already re-derives per instance, so it scales for free.

## 7. Lifecycle: publish as a computed policy

Per-instance `published: bool` flags do not scale to ~700. Replace with a predicate:

> **`publishable(member, sector) = the member has ≥ 1 relevant program feeding the sector`** (supply-existence). A **member is live** if it has ≥ 1 such sector.

This is the §2 supply-sparsity prune used as the gate — maximal coverage, no quality threshold. It supersedes the manual `published` flags in `partnerships/landscape.py` and `atlas/college-atlas/partnerships/landscapeInstances.ts`, and the client-side `DraftGate` becomes a check against this computed catalog rather than hand-set booleans. (Thin coverage stays visible — "honest, not broken" — because the bar is *existence*, not richness.)

## 8. Routing & surface (frontend)

**Existing URLs are preserved (per §1a); the scaling route is additive.** Two facts shape the design. First, `DraftGate` already makes the static-export HTML **inert** (`viewable && mounted` → `null` at build), so pre-rendering each instance emits identical empty shells — per-instance pre-render buys nothing, the dashboard is client-rendered against `/partnerships/{id}`. Second, the only obstacle to *flat* landscape URLs at scale is the `app/[collegeId]` root-slot collision (existing flat URLs win today only because they are hardcoded folders).

Two options, both keeping existing URLs byte-identical:

| | Existing URLs | New-view URLs | Touches existing routes |
|---|---|---|---|
| **A. Additive (recommended)** | untouched | nested: `/landscape/<member>/<sector>` | no — zero regression risk |
| **B. Root dispatcher** | flat, preserved | flat: `/foothill-biotech` | yes — `[collegeId]` dispatches college-or-landscape |

Flat URLs for *new* views are impossible without generalizing the `[collegeId]` slot (Next routing precedence). So: **A** preserves everything by touching nothing (two schemes coexist, but new views have no prior URL to regress); **B** keeps one uniform flat scheme but refactors the existing college + landscape routing and so must be gated behind the Phase-0 characterization tests for both the college pages and the 12 landscape instances.

Recommendation: **A by default** (regression-proof). Adopt **B** only if a uniform flat scheme is worth the gated refactor. Either way:

- the new route is **one parameterized, client-rendered page** with `generateStaticParams` *generated* from the published catalog (§7) — not hand-authored folders;
- identity (`name`, `accent`, `shortTitle`, `swp_tag`, counties) is **derived** from `member.name` + `sector.{label,accent}`, and a `/partnerships/landscapes` index endpoint serves the catalog, killing the `landscapeInstances.ts` ↔ backend sync burden;
- the existing 12 hardcoded folders stay exactly as they are (12 is not a scale problem); the dynamic route carries only the new long tail.

## 9. Backend route scaling

`partnerships/api.py` registers routes by looping `routable_specs()` and calling `_register_landscape_routes(spec)` — fine for 11, but ~700 × 5 routes at boot strains startup + OpenAPI generation. At scale, collapse to **one dynamic `/partnerships/{id}/...`** that resolves the spec from the generator at request time. Keep the loop until N actually warrants the switch.

## 10. Performance

Low preview traffic today, but MCP changes the load profile (an LLM fans out queries a human would not). Recommendation: **on-demand assembly first**, with the **shared regional atoms cached** (`demand`, `employers` per region/sector — small, change only on a pipeline refresh). Promote to **materialized graph aggregation edges** (e.g. `(:College)-[:SUPPLY_IN {awards, enrollments}]->(:Sector)`, refreshed by a build step) **only when measured latency or MCP fan-out demands it** — keeping the "cube" in the graph, consistent with §5, not a separate store.

Prerequisite, not a cube: **investigate the known perf signals first** — the 2026-06-11 client-query OOM (heap 2 G) and the cold-cache 5–15 s reads. The latency problem may be one bad query or undersized heap/pagecache, not a missing precompute layer. Measure before building.

## 11. Build inventory (what's newly needed)

- **Member catalog** — `members.csv` (college, district, region, counties) + a loader producing `District`/`Region` nodes and `IN_DISTRICT` / `IN_REGION` edges; materialize the existing `COLLEGE_COE_REGION` map as edges.
- **`Member` abstraction** generalizing today's hand-defined `MemberSet` over the hierarchy.
- **`resolve_region` → `resolve_regions`** (per-region demand/employer union).
- **Generated `REGISTRY`** from members × sectors × supply-sparsity (replaces the hand-authored dict).
- **Gap measure in the projection layer** — generalize the Occupation Coverage trichotomy into the multi-level localization of §4, with a prioritization score.
- **Publish predicate** (§7) replacing manual `published` flags in `landscape.py` + `landscapeInstances.ts`.
- **Frontend** — one parameterized `app/landscape/[member]/[sector]/` route + a `/partnerships/landscapes` index endpoint; derive identity; retire the per-instance folders.
- **(Deferred) MCP server** — thin adapter over the projection functions + NL→Cypher.
- **(Deferred) precompute/materialization** — only when measured.
- **(Deferred) statewide demand union** — the multi-region aggregation.

## 12. Phasing

0. **Characterization snapshots (the regression gate, §1a).** Before touching the backend, capture the current outputs of all 12 live instances (SVAMP + 11 SMCCD) — landscape payload, occupation coverage states, employer sets — as committed fixtures. SVAMP already has golden snapshots; the 11 SMCCD views do not, and they are the ones most exposed to the `resolve_regions` refactor. Every later phase must keep these green. No refactor merges with a red characterization test.
1. **Member catalog in the graph** — unlocks everything; nothing else can aggregate over the hierarchy without it.
2. **Generalize the invariant + generate the registry** — `resolve_regions`, supply-sparsity enumeration.
3. **Gap analysis in the projection layer** — the telos; the multi-level localization and prioritization.
4. **Collapse routing + derived identity + `/landscapes` index** — frontend to one route, backend toward one dynamic route.
5. **Publish predicate** — supply-existence gate.
6. *(Deferred)* **MCP server** — once the projection layer is stable and the tool surface is decided.
7. *(Deferred)* **Precompute / materialize** — when latency or MCP fan-out is measured to demand it.

## 13. Risks & coexistence constraints

- **SVAMP is curated and golden-snapshot-pinned.** It uses the legacy division + `is_cte_top4_family` path, deliberately distinct from the sector-derived `vocational=True` path. The generated registry must let the hand-authored SVAMP spec coexist unchanged, or its golden tests break.
- **Build-time scaling** (if A1-style pre-render is ever chosen over the recommended single route) grows with the published count — the publish policy is then a build necessity, not only UX.
- **Statewide demand** is the one place the regional invariant genuinely bends; defer, but keep `resolve_regions` shaped for it.
- **Graph as single source of truth** means member edits flow through `members.csv` + a load, with the same `load_employers`-style "rebuilds edges" caution: prefer additive loads / surgical `SET` over wholesale rebuilds for the member layer.

## 14. Open decisions (still pending)

- **MCP tool surface** — deferred by product; the §4 gap functions (`gaps(member)`, `compare(members, sector)`) are the natural first-class tools once it's defined.
- **Gap prioritization formula** — the exact weighting of demand magnitude × feasibility × strategic fit.
- **District/Region as full graph nodes vs. lighter modeling** — leaning full nodes for MCP-queryability.
- **Statewide demand aggregation** — sum-to-state vs. per-region breakdown presentation.
