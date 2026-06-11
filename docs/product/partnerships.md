# Partnerships

Partnerships are the form Kallipolis is built to enable. The mission sentence names the activity directly: the product exists *for community colleges to forge stronger workforce partnerships with industry*. The other four units of analysis — students, courses, occupations, employers — are the analytical material; partnerships are what the analytical material directs work toward.

The Partnerships surface is the place where that material is composed into something the workforce development office can act on: a deterministic, per-occupation labor market alignment report that identifies the regional employers whose hiring profile makes them candidate partners for development of that occupational pathway.

## The essence

A Partnership Opportunity in Kallipolis is *occupation-centric*. The unit of analysis is a (college, SOC) pair, not a (college, employer) pair. The report frames an occupation in the regional labor market, characterizes the college's curricular coverage of it, and surfaces the regional employers hiring for it as candidate partners for a multi-employer engagement around the occupational pathway.

The shape is opinionated and intentional. California's Strong Workforce Program funds regional consortium projects — multi-college, multi-employer, organized around occupational pathways within the 12 PCAH-classified Doing-What-MATTERS sectors. A single-employer-centric "partnership" was always a dilution of how SWP actually structures grants; reshaping around occupational opportunity, with employers as the candidate target *set*, matches both how SWP funding is written and how regional COE plans frame their priorities. The product becomes the epistemic foundation for workforce development officers to reason about partnerships in the way the institutional context already does.

The formulation of high-quality occupation-centric partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to making this formulation possible.

## Navigation: sector → occupation

The Partnerships index is a sector accordion. Each row is one of the 12 Strong Workforce sectors classified by the Chancellor's Office Program and Course Approval Handbook (PCAH). Expanding a sector reveals the CTE-reachable occupations within it that the college's COE region demands, alphabetically ordered.

The mapping from sector to occupation is institutional: the PCAH file lists every TOP6 code classified as CTE under one of the 12 sectors; for each TOP6, the chain `TOP → CIP → SOC` (Chancellor's Office TOP-CIP crosswalk + BLS/NCES CIP-SOC crosswalk) yields the SOCs reachable from that program area. The intersection with the college's regional COE demand profile bounds each sector accordion to occupations the local labor market actually hires for.

A SOC reachable from multiple sectors' TOPs appears under each of them. This is honest to the institutional crosswalk — Welders is genuinely relevant to both Advanced Manufacturing and Energy/Construction/Utilities — and matches the multi-sector tagging the Employers surface uses.

Each occupation row carries enough metadata for the row to be self-describing: SOC code, title, the college's current course count for the SOC, and the count of regional employers hiring for it. Clicking the **Draft Partnerships** CTA navigates to the per-SOC opportunity report.

## What an Opportunity Report contains

The report is a deterministic per-(college, SOC) artifact. Five narrative sections argue the institutional case; structured evidence blocks ground each section. The narrative does meaning; the evidence does completeness.

### The four sections of the narrative

- **Executive summary.** Frames the occupation in its sector context, names the multi-employer engagement opportunity the alignment data identifies, and integrates the strongest signals from regional demand and curriculum coverage in compressed form. The reader finishes the paragraph understanding why this occupational pathway merits partnership development.

- **Occupational demand.** Establishes the regional labor market for the SOC: median annual wage and annual openings in the COE region, drawn directly from the Centers of Excellence published demand profile. The evidence block carries the wage, openings, regional employment, and 5-year growth rate for inspection.

- **Curriculum alignment.** Establishes the institutional pathway from the college's curriculum to the SOC via the Chancellor's Office TOP-CIP-SOC crosswalk. The evidence is the actual departments and courses whose `PREPARES_FOR` edge maps to the target SOC, grouped by department.

- **Partnership opportunities.** Names the regional employers hiring for the SOC as candidate partners for a multi-employer engagement around the occupational pathway. The evidence is the employer list, sorted by NAICS-4 industry-share — the BLS Occupational Employment Statistics measure of how prominent this role is within each employer's industry. The most "occupation-central" employers surface first.

The four sections compose three of the units of analysis (occupations, courses, employers) plus the synthesizing executive summary; the student pipeline, formerly a fifth section, is omitted in the current non-PII configuration (see [students](./students.md)). Employers, formerly the *subject* of the artifact, are now the candidate set the artifact directs the coordinator toward — the multi-employer engagement opportunity the data identifies.

### Strong Workforce evidence

The report carries a tabular Strong Workforce evidence block — the regional supply-demand foundation any subsequent funding justification requires. Demand is the regional annual openings for the selected SOC; supply is the projected annual program completions for the TOPs the institutional crosswalk maps to that SOC; the gap is their difference. The block has no narrative; it is data only.

This is what makes the artifact institutionally legible to the Strong Workforce Program without making the artifact itself an SWP application. NOVA submission remains a coordinator-led act; Kallipolis provides the empirical foundation that any submission depends on.

## How Opportunity Reports are generated

The methodology is fully deterministic. Same college and same SOC always yield byte-identical prose. There is no LLM call at runtime; every claim is a function of the institutional graph plus the COE-published regional figures.

**Sector index assembly** ([`backend/partnerships/opportunity.py`](../../backend/partnerships/opportunity.py), `build_sector_index`). Composes PCAH TOP→Sector, the CTE-reachable SOC universe via `cte_reachable_socs`, the college's regional COE demand profile, and the college's `PREPARES_FOR` edge set into the sector accordion. Each occupation row's course count and employer count is derived from a single Cypher pass against the graph.

**Per-SOC report assembly** (same file, `build_opportunity_report`). For a given (college, SOC) pair, gathers occupation metadata from the graph, regional demand from COE, TOP-grouped curriculum coverage from the existing `_gather_aligned_curriculum` helper, and the candidate employer set from the `oes_socs_for_naics4` industry-share pivot. The narrative is composed by deterministic templates in [`backend/partnerships/opportunity_narrative.py`](../../backend/partnerships/opportunity_narrative.py).

**Endpoints**:

| Method | Path | Returns |
|---|---|---|
| GET | `/partnerships/sectors` | `SectorIndex` (the accordion) |
| GET | `/partnerships/opportunity/{soc_code}` | `OpportunityReport` (the per-SOC artifact) |

Both are `GET`-shaped because they're idempotent and cacheable. The frontend fetches each on view mount; the deep-link URL `/{collegeId}/partnerships/opportunity?soc={soc}` makes any specific report shareable for grant applications and internal correspondence.

### Trust through visibility

The report is composed deterministically because the audience needs to trust the institutional data, not the system. Each narrative section is followed immediately by the empirical material that supports it. The coordinator reads the claim about regional demand and then sees the wage, openings, employment, and growth figures. They read the curriculum alignment claim and then see the actual courses, with TOP code attribution. They read the partnership opportunities framing and then see the actual employer list with NAICS industry-share figures.

This is the architectural commitment: the narrative is *grounded* by being composed deterministically from the empirical material it interpolates and by being immediately followed by that material. The coordinator is not asked to trust Kallipolis. They are asked to trust the Chancellor's Office TOP-CIP crosswalk, the BLS/NCES CIP-SOC crosswalk, the COE regional demand publication, the BLS OEWS Industry-Occupation Matrix, and the PCAH sector classification — all named external sources cited in the artifact.

## How the partnerships flow will evolve

The current implementation surfaces partnership *opportunities* — the data-driven foundation a workforce development officer reasons about partnership development from. The artifact is identification, not management.

The natural next vertical slice is partnership *as a managed entity*: each row in a report's Partnership Opportunities section becomes a candidate that, in a later product state, carries status (identified → contacted → engaged → MOU → active), history (last touchpoint, prior engagements), and provenance (which alignment report surfaced this candidate, when). That extends Kallipolis from labor market intelligence into the operational lifecycle of partnerships themselves.

A second possible direction is productized SWP application generation — turning the regional supply-demand evidence block into a NOVA-shaped submission. The current report carries the empirical foundation any SWP project narrative requires; a templated NOVA-shaped output is one transformation away.

Both directions are real architectural possibilities and both will be informed by what coordinators actually request after working with the identification artifact. The current shift establishes the ontological groundwork: partnerships are first-class entities born from occupation-anchored opportunities, not from employer-anchored asks. Future surfaces inherit the same data foundation and the same deterministic engine.

## The core value proposition

Partnerships unify their angles around a single observation: the formulation of data-driven, occupation-centric partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to enabling it. The four units of analysis provide the empirical material. The institutional TOP-CIP-SOC crosswalk provides the bridge that joins curriculum to labor market without an internally-derived interpretive layer in between. The PCAH sector classification provides the institutional vocabulary the workforce development office already speaks. The BLS OEWS industry-share pivot identifies the candidate employer set whose hiring profile makes them strategic partners for a given occupational pathway.

Everything upstream of the Partnerships node is preparation. The Partnerships node itself is the moment Kallipolis does its job — the moment a workforce development officer sees, deterministically and reproducibly, a data-driven case for convening regional employers around the development of a specific occupational pathway in their service area.
