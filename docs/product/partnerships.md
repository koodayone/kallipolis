# Partnerships

Partnerships are the form Kallipolis is built to enable. The mission sentence names the activity directly: the product exists *for community colleges to forge stronger workforce partnerships with industry*. The other four units of analysis — students, courses, occupations, employers — are the analytical material; partnerships are what the analytical material directs work toward.

The Partnerships surface is where that material is composed into something a workforce development office can act on. It is organized as a **landscape**: a college — seen inside its regional consortium — laid across a Strong Workforce sector, so a coordinator can read at a glance where the college's programs meet regional demand, which neighboring colleges serve the same occupations, and where the openings for cross-college partnership lie.

## The essence

A Partnership Opportunity in Kallipolis is *occupation-centric* and *consortium-aware*. The unit of analysis is a (college, occupation) pair, not a (college, employer) pair — and the college is never shown alone.

The shape is opinionated and intentional. California's Strong Workforce Program funds *regional consortium* projects: multi-college, multi-employer, organized around occupational pathways within the 12 PCAH-classified Doing-What-MATTERS sectors. A single-employer, single-college "partnership" was always a dilution of how SWP actually structures grants. Reshaping the surface around a member read against a sector — with employers as the candidate target *set* and neighboring colleges as candidate *collaborators* — matches both how SWP funding is written and how regional Centers of Excellence plans frame their priorities. The product becomes the epistemic foundation for workforce development officers to reason about partnerships in the way the institutional context already does.

## The landscape: a college inside its consortium

The surface is a **member × sector landscape**. A member is a single college, a district, or a regional consortium; a sector is one of the 12 PCAH Strong Workforce sectors. Choosing both resolves the programs and occupations that sector comprises for that member.

At its center is the **coverage matrix**: programs (TOP6) down the rows, colleges across the columns. For a single college the columns are the college *and its regional peers* — the other colleges in the consortium that offer overlapping programs. This is the partnership-discovery mechanism the surface exists for: reading across a program's row shows every college in the region training for the same occupations, which is exactly where cross-college collaboration — shared curriculum, articulated pathways, joint employer engagement — becomes visible. Each cell is shaded by coverage: the college both graduates completers *and* currently enrolls students (covered), one signal but not the other (partial), or neither against real regional demand (a gap).

Supply and demand sit on either side of the matrix, owned by different axes and never conflated. **Supply** — projected annual program completions, a three-year average over the crosswalk's feeder programs — is a property of programs and sums cleanly across colleges. **Demand** — regional annual openings and wages, from the Centers of Excellence — is a property of occupations and is regional; it is shown per occupation and never summed across the occupations a program feeds, because the TOP-CIP-SOC crosswalk is many-to-many and summing would double-count.

The landscape is read through three **lenses** — Programs (the coverage matrix), Occupations (the regional demand the sector's occupations carry), and Employers (the regional firms hiring for them) — and an **industry rail** across the top switches the member between the sectors it is actively in, without leaving the view. Every view — a single college reading itself and a consortium reading its region alike — shows the occupations the member actually serves, surfacing the *in-demand* ones (those clearing the region's openings and wage floors) by default and collapsing the rest a click away, so a curated priority reads as a priority rather than a hidden gap. The in-demand set is the regional priority-job curation that names where partnership coordination is worth brokering; it leads every view as a highlighted default rather than a hard filter, so the fuller footprint is folded, never deleted. Each occupation row carries its regional demand inline — annual openings and median wage — so the demand sort the rows follow is legible on the row itself.

## The occupation drill: a partnership opportunity report

Selecting a coverage cell drills into the occupation as a deterministic per-(college, SOC) **opportunity report**, rendered inline. It frames the occupation in the regional labor market, characterizes the college's curricular coverage of it, and surfaces the regional employers hiring for it as candidate partners for a multi-employer engagement around the pathway.

### The sections of the narrative

- **Executive summary.** Frames the occupation in its sector context, names the multi-employer engagement opportunity the alignment data identifies, and integrates the strongest signals from regional demand and curriculum coverage in compressed form.

- **Occupational demand.** Establishes the regional labor market for the SOC: median annual wage and annual openings in the COE region, drawn directly from the Centers of Excellence published demand profile.

- **Curriculum alignment.** Establishes the institutional pathway from the college's curriculum to the SOC via the Chancellor's Office TOP-CIP-SOC crosswalk — the actual departments and courses whose `PREPARES_FOR` edge maps to the target SOC.

- **Partnership opportunities.** Names the regional employers hiring for the SOC as candidate partners, sorted by NAICS-4 industry-share — the BLS Occupational Employment Statistics measure of how prominent this role is within each employer's industry. The most "occupation-central" employers surface first.

Employers, formerly the *subject* of the artifact, are the candidate set the artifact directs the coordinator toward; the neighboring colleges the coverage matrix surfaces are the candidate collaborators. Together they are the multi-employer, multi-college engagement the Strong Workforce Program is written to fund.

### Strong Workforce evidence

The report carries a tabular Strong Workforce evidence block — the regional supply-demand foundation any subsequent funding justification requires. Demand is the regional annual openings for the selected SOC; supply is the projected annual program completions for the TOPs the institutional crosswalk maps to that SOC; the gap is their difference. The block has no narrative; it is data only.

This is what makes the artifact institutionally legible to the Strong Workforce Program without making the artifact itself an SWP application. NOVA submission remains a coordinator-led act; Kallipolis provides the empirical foundation any submission depends on.

## How the landscape is composed

The methodology is fully deterministic. The same coordinate always yields byte-identical output. There is no LLM call at runtime; every figure is a function of the institutional graph plus the COE-published regional figures.

- **The landscape** ([`backend/partnerships/landscape_build.py`](../../backend/partnerships/landscape_build.py), `build_landscape`; and [`landscape_programs.py`](../../backend/partnerships/landscape_programs.py) for the coverage matrix) resolves a member×sector spec into the coverage grid, supply treemap, and per-lens data. Supply is routed off the SOC's crosswalk feeder set — the one supply basis — so a program that confers a credential without a course tagged to its own code still counts.

- **The occupation drill** ([`opportunity.py`](../../backend/partnerships/opportunity.py), `build_opportunity_report`) composes, for a (college, SOC) pair, occupation metadata and regional demand from the graph, TOP-grouped curriculum coverage, and the candidate employer set from the BLS OEWS industry-share pivot; the narrative is composed by deterministic templates in [`opportunity_narrative.py`](../../backend/partnerships/opportunity_narrative.py). It is rendered *inline* in the landscape (`OpportunityReportBody`), not as a separate page.

**Endpoints** (mounted at `/partnerships`; see [API reference](../architecture/api-reference.md)):

| Method | Path | Returns |
|---|---|---|
| GET | `/partnerships/{instance}/programs` | the member×sector coverage landscape |
| GET | `/partnerships/opportunity/{soc_code}` | the per-(college, SOC) opportunity report (embedded drill) |

### Trust through visibility

The report is composed deterministically because the audience needs to trust the institutional data, not the system. Each narrative section is followed immediately by the empirical material that supports it — the reader sees the wage and openings behind the demand claim, the actual courses behind the alignment claim, the employer list with NAICS industry-share behind the partnership framing.

The coordinator is not asked to trust Kallipolis. They are asked to trust the Chancellor's Office TOP-CIP crosswalk, the BLS/NCES CIP-SOC crosswalk, the COE regional demand publication, the BLS OEWS Industry-Occupation Matrix, and the PCAH sector classification — all named external sources cited in the artifact.

## How the partnerships flow will evolve

The current implementation surfaces partnership *opportunities* — the data-driven foundation a workforce development officer reasons about partnership development from. The artifact is identification, not management.

The natural next vertical slice is partnership *as a managed entity*: each candidate — an employer to convene or a college to collaborate with — carrying status (identified → contacted → engaged → MOU → active), history, and provenance (which coordinate surfaced it, when). That extends Kallipolis from labor market intelligence into the operational lifecycle of partnerships themselves.

A second direction is productized SWP application generation — turning the regional supply-demand evidence into a NOVA-shaped submission. The report already carries the empirical foundation any SWP project narrative requires; a templated output is one transformation away.

A third, opened by the consortium framing itself: the peer view is currently strongest in the Bay Area, where the consortium's occupational clusters are computed; extending that regional-peer analysis statewide would make cross-college partnership discovery uniform across every California region.

## The core value proposition

Partnerships unify their angles around a single observation: the formulation of data-driven, occupation-centric, consortium-aware partnership opportunities is the core value proposition of Kallipolis, and the entire ontology is dedicated to enabling it. The four units of analysis provide the empirical material. The institutional TOP-CIP-SOC crosswalk joins curriculum to labor market without an interpretive layer in between. The PCAH sector classification provides the institutional vocabulary the workforce development office already speaks. The coverage matrix reveals the regional colleges serving the same occupations; the BLS OEWS industry-share pivot identifies the employers whose hiring profile makes them strategic partners.

Everything upstream of the Partnerships node is preparation. The Partnerships node itself is the moment Kallipolis does its job — the moment a workforce development officer sees, deterministically and reproducibly, a data-driven case for convening regional employers *and* neighboring colleges around the development of a specific occupational pathway in their service area.
