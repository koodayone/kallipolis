# Graph Model

The Kallipolis ontology is implemented as a Neo4j property graph with seven node types and nine relationship pairings. This document describes the schema — what each node type represents, what each relationship encodes, and how the supply-demand chain is realized in actual graph structure.

## The seven node types

Four node types live on the curriculum side, three on the industry side. Each one corresponds to a concept in the product section.

### Curriculum side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **College** | name, city, state, region | `name UNIQUE` | A California community college |
| **Department** | name | `name UNIQUE` | A department within a college (e.g., Welding, Nursing) |
| **Course** | code, college, name, department, catalog_section, units, description, prerequisites, learning_outcomes, course_objectives, transfer_status, url, top_code, is_cte | `(code, college) UNIQUE` | A course actually taught at a college. `top_code` is the per-college 6-digit TOP6 from the Chancellor's Office Master Course File. `department` is derived from `top_code` via the Chancellor's Office Taxonomy of Programs Manual (TOP4 → name). `catalog_section` preserves the section header Gemini extracted from the source PDF for traceability. `is_cte` is true iff `top_code` appears in the PCAH "TOP Codes to Sectors" file — the institutional definition of CTE scope. |
| **Student** | uuid, gpa, primary_focus, primary_top6, courses_completed, college | `uuid UNIQUE` | A student enrolled at a college (synthetic). The derived fields are materialized after enrollment generation; `primary_top6` is the 6-digit TOP code the student concentrates in, authoritatively keying the `primary_focus` department label. `college` records the institution the student attends — the partnership-positioning question (a college's pipeline for a SOC) is per-college, so this property scopes the HAS_COMPETENCY-pivoted reads in `backend/partnerships/gather.py` to one college's ~13K students rather than the system-wide pool of 400K+. Multi-college future: convert to a list. |

### Industry side

| Node | Key properties | Constraint | What it represents |
|---|---|---|---|
| **Region** | name, display_name, priority_sectors | `name UNIQUE` | A regional labor market. The `priority_sectors` list property names the SWP priority industry sectors from the region's Strong Workforce Program development plan. |
| **Occupation** | soc_code, title, description, education_level | `soc_code UNIQUE` | A SOC-coded occupation in regional demand. Wage and employment data live on the `DEMANDS` edge, not on the node, because the same occupation has different demand profiles in different regions. |
| **Employer** | name, sector, swp_sectors, naics4, description, website, operations_summary | `name UNIQUE` | A real organization that hires in California. `sector` is the NAICS-2 display label; `swp_sectors` is the canonical PCAH sector list (see [SWP Sector NAICS Composition](../pipeline/swp-sector-naics.md)), loaded from the same xlsx the occupation side uses. `naics4` is the BLS-published 4-digit NAICS industry code; it keys the BLS OEWS National Industry-Occupation Matrix that bounds the `HIRES_FOR` SOC pool (see [Institutional Deference Evolution](./institutional-deference-evolution.md)). The `website` property is the verified official URL produced by the validation step in the [employer generation pipeline](../pipeline/employer-generation.md). The `operations_summary` property is a verb phrase characterizing the employer's operations (e.g., "operates an all-boys Jesuit private high school in San Jose, serving approximately 1,600 students"), pre-computed once per employer at ingestion by [`backend/employers/characterize.py`](../../backend/employers/characterize.py) and consumed by the deterministic partnership-proposal narrative templates so the executive-summary opening sentence is institutionally consistent across runs. |

The seven node types map cleanly to the conceptual structure documented in the product section. The four units of analysis — students, courses, occupations, employers — each have a node type. The structural elements — colleges and departments on the curriculum side, regions on the industry side — are containers. The bridge between curriculum and labor market is encoded directly as an edge between Course and Occupation, derived from the institutional TOP-CIP-SOC crosswalk; no internally-derived skill index sits between them.

## The nine relationship pairings

Relationships encode the supply-demand logic of workforce development. Each one is directional and most carry no properties.

| Relationship | From → To | Properties | What it encodes |
|---|---|---|---|
| `OFFERS` | College → Department | — | A college operates a department |
| `CONTAINS` | Department → Course | — | A department offers a course |
| `ENROLLED_IN` | Student → Course | grade, term, status | A student is or was enrolled in a course |
| `IN_MARKET` | College → Region | — | A college operates within a regional labor market |
| `IN_MARKET` | Employer → Region | — | An employer operates within a regional labor market |
| `DEMANDS` | Region → Occupation | employment, annual_wage, growth_rate, annual_openings | A region has demand for an occupation, with the regional employment, wage, growth, and openings metadata that varies by region |
| `HIRES_FOR` | Employer → Occupation | pct_total | An employer hires for an occupation. Derived deterministically from the BLS OEWS National Industry-Occupation Matrix: every SOC the matrix publishes at `pct_total > 0` for the employer's `naics4` becomes a `HIRES_FOR` edge, and the published share is persisted as the `pct_total` edge property. No LLM in the loop on the inclusion decision. The shape per employer is therefore the BLS-published occupational composition of the employer's industry; per-employer specificity is carried by the parallel `IDENTITY_HIRES_FOR` overlay. |
| `IDENTITY_HIRES_FOR` | Employer → Occupation | — | An LLM-curated overlay on `HIRES_FOR`. The 3–8 SOCs (drawn from the same OEWS NAICS-bounded pool) that Pass 2b of [`backend/employers/enrich.py`](../../backend/employers/enrich.py) selected as most characteristic of this specific employer based on their website's careers/jobs/team content. Always a subset of the employer's `HIRES_FOR` set. Empty for employers whose website couldn't be enriched (no probe pass), which is the explicit cost of confining LLM judgment to identity refinement rather than inclusion. |
| `PREPARES_FOR` | Course → Occupation | via_top | The institutional Course→Occupation crosswalk: a course's TOP code maps through CIP to the occupations its program institutionally prepares students for. Materialized from `Course.top_code` via the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks. The bridge edge between curriculum and labor market. |
| `HAS_COMPETENCY` | Student → Occupation | competency_depth, via_tops | A derived analytical edge: a student has demonstrated some level of competency development for an occupation iff at least one course they have ENROLLED_IN PREPARES_FOR that occupation. `competency_depth` is the count of distinct prep-tagged courses (the spectrum measure: 1 = beginning, N = substantial coursework). `via_tops` is the distinct TOP6 codes that mediated the crosswalk pathway. Cross-college by design: aggregates over a student's full enrollment history regardless of which colleges contributed which courses. Materialized at pipeline reload by [`backend/partnerships/compute.py`](../../backend/partnerships/compute.py); replaces a request-time `Student × ENROLLED_IN × PREPARES_FOR` cartesian that dominated the cost of `/partnerships/opportunity/{soc}`. |
| `PARTNERSHIP_ALIGNMENT` | College → Employer | roles_count, aligned_roles_count, aligned_course_count | A derived analytical edge: per-(college, employer) precomputed alignment summarizing how the college's curriculum prepares students for the employer's hire-occupation set. Powers `/employers/` ranking. Materialized at pipeline reload by [`backend/partnerships/compute.py`](../../backend/partnerships/compute.py). Replaces a request-time `College → Region → Employer × Occupation × PREPARES_FOR × CONTAINS` traversal. |
| `OCCUPATION_PIPELINE` | College → Occupation | course_count, employer_count, student_count, top_codes | A derived analytical edge: per-(college, SOC) precomputed aggregates for the partnerships sector index — count of aligned courses at the college, employers in the region hiring for the SOC, students in aligned departments, and the TOP6 codes mediating the alignment. Powers `/partnerships/sectors`. Materialized at pipeline reload by [`backend/partnerships/compute.py`](../../backend/partnerships/compute.py). Replaces three per-SOC traversals at request time. |

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
   │                                            ▲                          ▲
   │                                 ENROLLED_IN│                  HIRES_FOR
   │                                            │                          │
   │                                         Student                    Employer
   │                                                                       │
   ├──IN_MARKET──▶ Region ◀───────────IN_MARKET─────────────────────────────┤
                     │                                                     │
                     │DEMANDS                                              │
                     ▼                                                     │
                  Occupation ◀──────────────────────────────────────────────
```

The diagram shows the two halves of the graph meeting at `Occupation`. Read left to right, the diagram traces the supply chain: a college offers departments, departments contain courses, courses prepare students for occupations through the institutional crosswalk, students enroll in courses. Read right to left from the occupation layer, it traces the demand chain: regions demand occupations, employers hire for occupations. The two chains meet at the occupation node, with `PREPARES_FOR` carrying the institutional bridge that makes the supply-demand alignment computable.

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

- The **four units of analysis** correspond to the four foundational node types: `Student`, `Course`, `Occupation`, `Employer`. Each one is uniquely constrained, has its own institutional authority, and serves as a substantive entity rather than a structural one.
- **`College`, `Department`, and `Region`** are containers — they organize the foundationals into groupings that the user navigates through but does not act on directly.
- **`PREPARES_FOR`** is the bridge edge. It is real and load-bearing in the graph, but it has no institutional authority of its own beyond the named crosswalks it composes. Its existence is derived from the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC mappings.
- The **unit of action** — partnerships — is not stored as a node type. It is computed from traversals over the seven node types. A partnership opportunity is the result of a query that joins curriculum to labor market through `PREPARES_FOR`, plus a tabular regional supply-demand evidence block assembled from COE-published completions and demand projections. The graph is what makes the partnership artifact computable, even though it has no table of its own.
