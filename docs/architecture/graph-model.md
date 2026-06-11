# Graph Model

The Kallipolis ontology is implemented as a Neo4j property graph with seven node types — the six analytical and structural types plus the **Program** node — two shared time-dimension nodes (AcademicYear, Term), and the relationship set described below. This document describes the schema — what each node type represents, what each relationship encodes, and how the supply-demand chain is realized in actual graph structure.

## The node types

Four node types live on the curriculum side, three on the industry side, plus two shared time-dimension nodes. Each substantive type corresponds to a concept in the product section.

### Curriculum side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **College** | name, city, state, region | `name UNIQUE` | A California community college |
| **District** | name | `name UNIQUE` | A CCCCO community college district — the institutional grouping above a college (e.g., Foothill-De Anza CCD). The middle tier of the `college ⊂ district ⊂ region` member hierarchy the aggregated-landscape engine rolls supply up over. Sourced from the on-disk college catalog (`backend/pipeline/catalog_sources.json`) and materialized by [`backend/ontology/districts.py`](../../backend/ontology/districts.py). |
| **Department** | name | `name UNIQUE` | A department within a college (e.g., Welding, Nursing) |
| **Course** | code, college, name, department, catalog_section, units, description, prerequisites, learning_outcomes, course_objectives, transfer_status, url, top_code, is_cte | `(code, college) UNIQUE` | A course actually taught at a college. `top_code` is the per-college 6-digit TOP6 from the Chancellor's Office Master Course File. `department` is derived from `top_code` via the Chancellor's Office Taxonomy of Programs Manual (TOP4 → name). `catalog_section` preserves the section header Gemini extracted from the source PDF for traceability. `is_cte` is true iff `top_code` appears in the PCAH "TOP Codes to Sectors" file — the institutional definition of CTE scope. |
| **Program** | college, top6, name, top4, is_cte | `(college, top6) UNIQUE` | A TOP6 program at a college — the unit the Strong Workforce Program funds and reports on, instantiated as a first-class node (previously smeared across `Course.top_code`, `Student.primary_top6`, and the TOP4-derived Department). Keyed per-college, mirroring Course's compound key. Loaded from Chancellor's Office DataMart MIS exports by [`backend/ontology/programs.py`](../../backend/ontology/programs.py); award and enrollment measures hang off it as edges to shared time-dimension nodes (measure-on-edge, mirroring `DEMANDS`). Introduced additively — `PREPARES_FOR` stays on Course. |

### Industry side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **Region** | name, display_name, priority_sectors | `name UNIQUE` | A regional labor market. The `priority_sectors` list property names the SWP priority industry sectors from the region's Strong Workforce Program development plan. |
| **Occupation** | soc_code, title, description, education_level | `soc_code UNIQUE` | A SOC-coded occupation in regional demand. Wage and employment data live on the `DEMANDS` edge, not on the node, because the same occupation has different demand profiles in different regions. |
| **Employer** | name, sector, swp_sectors, naics4, description, website, operations_summary, lat, lng | `name UNIQUE` | A real organization that hires in California. `sector` is the NAICS-2 display label; `swp_sectors` is the canonical PCAH sector list (see [SWP Sector NAICS Composition](../pipeline/swp-sector-naics.md)), loaded from the same xlsx the occupation side uses. `naics4` is the BLS-published 4-digit NAICS industry code; it keys the BLS OEWS National Industry-Occupation Matrix that bounds the `HIRES_FOR` SOC pool (see [Institutional Deference Evolution](./institutional-deference-evolution.md)). The `website` property is the verified official URL produced by the validation step in the [employer generation pipeline](../pipeline/employer-generation.md). The `operations_summary` property is a verb phrase characterizing the employer's operations (e.g., "operates an all-boys Jesuit private high school in San Jose, serving approximately 1,600 students"), pre-computed once per employer at ingestion by [`backend/employers/characterize.py`](../../backend/employers/characterize.py) and consumed by the deterministic partnership-proposal narrative templates so the executive-summary opening sentence is institutionally consistent across runs. The `lat`/`lng` properties are the geocoded coordinates of the employer's street address, resolved by [`backend/employers/geocode.py`](../../backend/employers/geocode.py) into a decoupled `backend/employers/geocode_cache.json` (keyed by EDD `emp_id` so it survives employer-set regeneration) and joined onto the node at load; they position the employer on the regional employer map and are null for employers without a resolvable address. |

### Time-dimension nodes

Shared, uniquely-indexed nodes that program measures attach to (measure-on-edge, mirroring how `DEMANDS` carries wage/employment on the Region edge). A handful of nodes each, so the loader `MERGE` is an index seek, not a scan.

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **AcademicYear** | year | `year UNIQUE` | An award year (e.g., `2024-2025`); the shared target of `AWARDED` edges. |
| **Term** | term | `term UNIQUE` | An enrollment term (e.g., `Fall 2024`); the shared target of `ENROLLED` edges. |

The eight substantive node types map to the conceptual structure documented in the product section. Three of the four units of analysis — courses, occupations, employers — have a node type; the fourth, **students**, has no node in the current [non-PII configuration](../product/students.md) (its node and enrollment edges were removed). `Program` instantiates the TOP6 program that the curriculum side reports and funds on. The structural elements — colleges, districts, and departments on the curriculum side, regions on the industry side, and the AcademicYear/Term time dimensions — are containers. The bridge between curriculum and labor market is encoded directly as an edge between Course and Occupation, derived from the institutional TOP-CIP-SOC crosswalk; no internally-derived skill index sits between them.

## The relationships

Relationships encode the supply-demand logic of workforce development. Each one is directional and most carry no properties.

| Relationship | From → To | Properties | What it encodes |
|---|---|---|---|
| `OFFERS` | College → Department | — | A college operates a department |
| `CONTAINS` | Department → Course | — | A department offers a course |
| `IN_DISTRICT` | College → District | — | A college belongs to a CCCCO district. The middle tier of the institutional member hierarchy (`college ⊂ district ⊂ region`); a district inherits its region from its colleges' `IN_MARKET` edges. Materialized by [`backend/ontology/districts.py`](../../backend/ontology/districts.py) from the on-disk college catalog. |
| `IN_MARKET` | College → Region | — | A college operates within a regional labor market |
| `IN_MARKET` | Employer → Region | — | An employer operates within a regional labor market |
| `DEMANDS` | Region → Occupation | employment, annual_wage, growth_rate, annual_openings | A region has demand for an occupation, with the regional employment, wage, growth, and openings metadata that varies by region |
| `HIRES_FOR` | Employer → Occupation | pct_total | An employer hires for an occupation. Derived deterministically from the BLS OEWS National Industry-Occupation Matrix: every SOC the matrix publishes at `pct_total > 0` for the employer's `naics4` becomes a `HIRES_FOR` edge, and the published share is persisted as the `pct_total` edge property. No LLM in the loop on the inclusion decision. The shape per employer is therefore the BLS-published occupational composition of the employer's industry; per-employer specificity is carried by the parallel `IDENTITY_HIRES_FOR` overlay. |
| `IDENTITY_HIRES_FOR` | Employer → Occupation | — | An LLM-curated overlay on `HIRES_FOR`. The 3–8 SOCs (drawn from the same OEWS NAICS-bounded pool) that Pass 2b of [`backend/employers/enrich.py`](../../backend/employers/enrich.py) selected as most characteristic of this specific employer based on their website's careers/jobs/team content. Always a subset of the employer's `HIRES_FOR` set. Empty for employers whose website couldn't be enriched (no probe pass), which is the explicit cost of confining LLM judgment to identity refinement rather than inclusion. |
| `PREPARES_FOR` | Course → Occupation | via_top | The institutional Course→Occupation crosswalk: a course's TOP code maps through CIP to the occupations its program institutionally prepares students for. Materialized from `Course.top_code` via the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks. The bridge edge between curriculum and labor market. |
| `PARTNERSHIP_ALIGNMENT` | College → Employer | roles_count, aligned_roles_count, aligned_course_count | A derived analytical edge: per-(college, employer) precomputed alignment summarizing how the college's curriculum prepares students for the employer's hire-occupation set. Powers `/employers/` ranking. Materialized at pipeline reload by [`backend/partnerships/compute.py`](../../backend/partnerships/compute.py). Replaces a request-time `College → Region → Employer × Occupation × PREPARES_FOR × CONTAINS` traversal. |
| `OCCUPATION_PIPELINE` | College → Occupation | course_count, employer_count, top_codes | A derived analytical edge: per-(college, SOC) precomputed aggregates for the partnerships sector index — count of aligned courses at the college, employers in the region hiring for the SOC, and the TOP6 codes mediating the alignment. Powers `/partnerships/sectors`. Materialized at pipeline reload by [`backend/partnerships/compute.py`](../../backend/partnerships/compute.py). Replaces per-SOC traversals at request time. |
| `HAS_PROGRAM` | Department → Program | — | A department (TOP4) contains a TOP6 program. Additive alongside `CONTAINS`: the Program node was introduced without reparenting the existing Department→Course hierarchy. Materialized by [`backend/ontology/programs.py`](../../backend/ontology/programs.py) where the TOP4 Department exists. |
| `AWARDED` | Program → AcademicYear | count, award_type | Actual credentials a program awarded in a year, from Chancellor's Office DataMart MIS — institutional ground truth complementing COE-projected supply. One edge per award type. Institutional and summable across colleges. |
| `ENROLLED` | Program → Term | count, credit_type | Section enrollment for a program in a term, from DataMart MIS — the leading-indicator enrollment trend. One edge per credit type. Institutional and summable across colleges. |

The `IN_MARKET` relationship is overloaded: the same edge type connects both colleges and employers to their regional labor markets. This works because the semantics are the same in both cases — the entity operates within the region — even though the entities being connected are different node types.

### The bridge edge: PREPARES_FOR

`PREPARES_FOR` is the load-bearing edge that bridges the curriculum and industry sides of the graph. It is materialized in [`backend/ontology/prepares_for.py`](../../backend/ontology/prepares_for.py) from each course's `top_code` property by composing two externally-authored crosswalks:

1. **TOP → CIP** — the California Community Colleges Chancellor's Office TOP-CIP crosswalk (loaded from `backend/ontology/data/top_cip_crosswalk.csv`).
2. **CIP → SOC** — the BLS/NCES CIP-SOC crosswalk (loaded from `backend/ontology/data/CIP2020_SOC2018_Crosswalk.xlsx`).

The composed mapping is exposed to the loader as `top6_to_soc()` in [`backend/ontology/crosswalks.py`](../../backend/ontology/crosswalks.py). For each (college, course) pair, the loader writes one `PREPARES_FOR` edge per SOC the course's TOP6 maps to, with the TOP6 stored on the edge as `via_top` for audit-trail attribution. Edges to occupations not present in the graph (excluded by the institutional CTE filter at occupation load time) are skipped.

The edge is institutional in two distinct senses. Its **existence** is institutional: a course points to an occupation only when the Chancellor's Office and BLS/NCES crosswalks both place the TOP→CIP→SOC chain. Its **provenance** is institutional too: every edge carries the TOP6 it traveled through, so any partnership artifact can attribute the pathway claim to its source publication.

## Schema diagram

```
College ──OFFERS──▶ Department ──CONTAINS──▶ Course ──PREPARES_FOR──▶ Occupation
   │                                                                       ▲
   │                                                                HIRES_FOR
   │                                                                       │
   │                                                                    Employer
   │                                                                       │
   ├──IN_MARKET──▶ Region ◀───────────IN_MARKET─────────────────────────────┤
                     │                                                     │
                     │DEMANDS                                              │
                     ▼                                                     │
                  Occupation ◀──────────────────────────────────────────────
```

The diagram shows the two halves of the graph meeting at `Occupation`. Read left to right, the diagram traces the supply chain: a college offers departments, departments contain courses, courses prepare students for occupations through the institutional crosswalk. Read right to left from the occupation layer, it traces the demand chain: regions demand occupations, employers hire for occupations. The two chains meet at the occupation node, with `PREPARES_FOR` carrying the institutional bridge that makes the supply-demand alignment computable.

## The Program layer

The Program node attaches under Department, parallel to Course — additively, without disturbing the existing curriculum hierarchy or the `PREPARES_FOR` bridge:

```
Department ──HAS_PROGRAM──▶ Program ──AWARDED──▶ AcademicYear
                                   └──ENROLLED──▶ Term
```

`Program` instantiates the TOP6 program (the unit SWP funds and reports on), keyed per-college. Its measures are dimensioned time-series at different grains — annual awards, per-term enrollment — so they live on edges to shared `AcademicYear`/`Term` nodes rather than as scalar properties, mirroring how `DEMANDS` carries region-varying wage/employment on its edge. Awards are actual completions (DataMart ground truth, a complement to the COE-projected supply the partnership artifact already carries); enrollment is the leading-indicator trend.

**Wage outcomes are deliberately not in the graph.** The DataMart wage export has no college dimension and per-college cohorts are small-n suppressed, so wages are modeled at the TOP6 grain as read-time reference data (`get_wage_outcomes` over `wage_outcomes_summary.csv`, mirroring `supply.py` / `get_coe_supply`), displayed per program and never summed (medians are non-additive). Moving wages into the graph is a documented future step (see the `get_wage_outcomes` docstring).

The Program layer is consumed by the `/svamp` aggregated landscape ([`backend/partnerships/svamp.py`](../../backend/partnerships/svamp.py)); the per-(college, occupation) partnership reports do not read it.

## The bridge logic

The point of the graph schema is to make a specific question answerable: *which regional employers hire for occupations that this college institutionally prepares students for?* The answer is computed by traversing the bridge that the schema constructs between the curriculum and industry sides.

A bridge occupation is one that appears on both sides — it is `HIRES_FOR`-related to at least one regional employer and `PREPARES_FOR`-related to at least one course at the college. Without bridge occupations, the graph would be two disconnected pairs (college-students-courses on one side, region-employers-occupations on the other). With them, the graph becomes a single connected structure in which a coordinator can traverse from a course to a regional employer through the occupation that connects them.

This is why grounding the bridge in the institutional TOP-CIP-SOC crosswalk is so consequential. The crosswalk is what guarantees that a course's outward-facing occupation set and an occupation's inward-facing course set are derived from the same externally-authored mapping. The previous architecture used an internally-derived skills index in the bridge position; the present architecture uses the Chancellor's Office and BLS/NCES crosswalks directly, which gives every bridge claim a named institutional source.

## Two illustrative traversals

**Workforce alignment** — what occupations match a college's curriculum:

```cypher
MATCH (c:College {name: $college})-[:IN_MARKET]->(r:Region)-[:DEMANDS]->(occ:Occupation)
      <-[:PREPARES_FOR]-(course:Course {college: $college})
RETURN occ.title, count(DISTINCT course) AS aligned_course_count
ORDER BY aligned_course_count DESC
```

This is the supply-demand chain traversed end to end. It starts at a college, follows `IN_MARKET` to the region, follows `DEMANDS` to occupations the region needs, and joins on courses at the same college whose TOP code institutionally prepares students for those occupations. The count of aligned courses is a measure of how deeply the college's curriculum prepares students for each occupation in the region.

**Curriculum gap** — what occupations the regional labor market needs that this college has no aligned program for:

```cypher
MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
WHERE NOT EXISTS { MATCH (:Course {college: $college})-[:PREPARES_FOR]->(occ) }
RETURN occ.title, occ.soc_code
```

This is the gap identification capability the [occupations product document](../product/occupations.md) names as the unique improvement vector for the occupation form. The traversal starts at an employer, follows `HIRES_FOR` to its occupations, and filters to occupations that no course at the target college institutionally prepares students for. The result is the set of curricular gaps that the partnership work could address.

## How the schema embodies the product framing

The graph schema is the operational expression of the conceptual structure documented in the product section.

- The **units of analysis** correspond to foundational node types. Three of the four — `Course`, `Occupation`, `Employer` — are present as nodes today, each uniquely constrained, with its own institutional authority, serving as a substantive entity rather than a structural one. The fourth, **`Student`**, is a unit of analysis with no node in the current [non-PII configuration](../product/students.md): the per-student layer was removed, and the supply-side signal it once carried is now read from the `Program` award/enrollment aggregates.
- **`College`, `Department`, and `Region`** are containers — they organize the foundationals into groupings that the user navigates through but does not act on directly.
- **`PREPARES_FOR`** is the bridge edge. It is real and load-bearing in the graph, but it has no institutional authority of its own beyond the named crosswalks it composes. Its existence is derived from the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC mappings.
- The **unit of action** — partnerships — is not stored as a node type. It is computed from traversals over the six node types. A partnership opportunity is the result of a query that joins curriculum to labor market through `PREPARES_FOR`, plus a tabular regional supply-demand evidence block assembled from COE-published completions and demand projections. The graph is what makes the partnership artifact computable, even though it has no table of its own.
