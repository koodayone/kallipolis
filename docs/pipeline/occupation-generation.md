# Occupation Generation

Occupations are the demand-side anchor of the Kallipolis graph. They are the pipeline's only entity grounded in a single institutional demand authority — the California Community Colleges' Centers of Excellence for Labor Market Research — and they are the only entity where the same SOC code carries different regional demand profiles in different parts of California. This document describes how the stage takes the COE demand feed, restricts it to the occupations the Centers of Excellence designate as middle-skill — the band the community college system targets — attaches human-readable descriptions from the BLS SOC 2018 vocabulary, and loads the result as `Region`, `Occupation`, and `DEMANDS` structures in the graph.

## Source

The Centers of Excellence publishes a per-region occupational demand dataset that lists, for every SOC code the COE tracks, the regional employment, median annual wage, five-year projected growth rate, annual openings, and the typical entry-level education required. The pipeline consumes this as a CSV whose rows are scoped to a (SOC, region) pair: one row per occupation per region. `backend/occupations/generate.py` parses the CSV, pivots the rows into per-occupation records with a `regions` map keyed by COE region code, and writes the result to `backend/occupations/occupations.json`.

COE is the sole source for occupation demand metrics. An earlier implementation parsed the EDD OEWS wage survey across 30 metropolitan statistical areas and fed it into the same graph, but OEWS was retired when the pipeline converged on COE as the authority. The retirement was deliberate: OEWS is a federal wage survey with no workforce-development filtering, so it carried a long tail of occupations (entry-level retail, doctorate-only research) that community colleges do not prepare students for and that would have concentrated alignment noise downstream. COE is scoped to the community-college workforce-development mission from the start and partitions California along the nine-region boundary the community college system itself uses.

For the broader institutional framing of COE as a data authority, see [Data Authorities](../domain/data-authorities.md).

## The ten regions

The COE publishes demand data for nine regional groupings plus one statewide rollup. The nine regions correspond to the Centers of Excellence for Labor Market Research, which are distinct from the EDD Labor Market Information metropolitan statistical areas the employers pipeline uses. The crosswalk between the two systems lives in `backend/ontology/regions.py`.

| Code | Display name |
|---|---|
| `Bay` | Bay Area |
| `CA` | California |
| `CVML` | Central Valley / Mother Lode |
| `FN` | Far North |
| `GS` | Greater Sacramento |
| `IE/D` | Inland Empire / Desert |
| `LA` | Los Angeles |
| `OC` | Orange County |
| `SCC` | South Central Coast |
| `SD/I` | San Diego / Imperial |

Every loaded occupation carries a demand row for every one of these ten regions. The `CA` row is the statewide rollup, which the graph treats as a tenth region alongside the nine COE regions rather than as a fallback or aggregate computed from the others. Colleges are linked to their primary COE region via an `IN_MARKET` edge using the `COLLEGE_COE_REGION` mapping in `backend/ontology/regions.py`.

## The middle-skill scope

Not every occupation in the COE feed belongs in a community college graph. The scope is the set of occupations the Centers of Excellence designate as **middle-skill** — occupations above a high-school baseline but below a bachelor's degree, the band the community college system targets. COE publishes this designation directly. The pipeline consumes it as the authority; it does not re-derive it.

Concretely, the occupation set is exactly the SOCs in the COE middle-skill demand publication, `backend/ontology/occupational_demand_middle_skill.csv` — a strict, same-vintage subset of the COE's all-occupations export. `backend/occupations/generate.py` is 1:1 with that file: every SOC it lists becomes a node, with no derived filter applied at generation time. Curation lives upstream, in the COE designation, not in a rule this stage recomputes.

This replaces an earlier COE-∩-CTE-reachable filter, which kept a SOC only if a PCAH-classified CTE TOP6 code reached it through the TOP→CIP→SOC crosswalk (composed by `cte_reachable_socs()` in `backend/ontology/crosswalks.py`). That rule had a two-sided error. It admitted occupations that are not middle-skill but happened to be crosswalk-reachable — management and professional roles the crosswalk over-reaches to — and it dropped middle-skill occupations the crosswalk could not reach: real regional demand, such as Home Health and Personal Care Aides or Clinical Laboratory Technologists, with no community-college program pathway in the crosswalk. Grounding the occupation set on the COE middle-skill designation resolves both, and separates two questions the crosswalk filter had conflated: *which occupations are community-college targets* (the COE designation, settled here) from *which occupations a program can prepare for* (crosswalk reachability, still used downstream to scope the Strong-Workforce sector analysis — see [Partnerships](../product/partnerships.md)).

The designation also captures California's CTE trades directly, where an earlier BLS "Typical Entry Level Education" proxy had miscoded them. Electricians, welders, plumbers, machinists, roofers, and cement masons all read as "high school diploma" or "no formal credential" in the BLS minimum-credential field, because their entry bar is a high school diploma plus apprenticeship or on-the-job training — yet they are central Strong Workforce occupations. COE's middle-skill designation, an institutional judgment rather than a federal statistical proxy, includes them.

## Sector categorization

The middle-skill scope settles *which* occupations the graph holds. A second COE publication settles *which* Strong Workforce sector each belongs to — the Centers of Excellence's Bay Region per-sector crosstabs, one file per CCCO sector, which list every occupation the COE places in that sector. Sector membership is the **join** of the two authorities: for every occupation in the middle-skill universe, its sector is the crosstab that lists it. The occupation→sector map is captured in `backend/partnerships/data/coe_occupation_sector.csv`, and `scripts/generate_sector_socs.py` joins it with `backend/occupations/occupations.json` to regenerate `backend/partnerships/data/sector_socs.csv`. The crosstabs partition SOC codes one-to-one, so each occupation resolves to exactly one sector; the universe is a subset of the mapped occupations, so every occupation is categorized and the sector set exactly covers the universe — no occupation is left unsectored.

The derivation deliberately keeps one thing a naive read of the crosstabs would drop. Each crosstab tags its rows with a skill level (Middle Skill / Below Middle Skill), and an earlier snapshot filtered sector membership to the Middle-Skill rows. But the middle-skill universe already scopes the occupation set; re-applying the skill filter at the sector stage dropped in-demand occupations the universe keeps — School Bus Drivers (`53-3051`) and Shuttle Drivers (`53-3053`), both prepared for by the vocational Truck and Bus Driving program (TOP `094750`, home sector Advanced Transportation & Logistics) at Bay Area colleges, yet tagged Below Middle Skill in the crosstab. Joining without the redundant filter lets the universe define the middle-skill boundary once, so those occupations land in their sector rather than being orphaned in the universe with no sector. Sector membership scopes the downstream Strong-Workforce sector analysis — see [Partnerships](../product/partnerships.md).

## How the stage runs

The stage runs three sub-steps end to end. The scripts are independent but share `occupations.json` as the handoff format.

**1. Parse.** `generate.py` reads the COE middle-skill CSV, coerces each row's employment/wage/growth/openings cells into typed values, and pivots the rows into per-occupation records. No filter runs here: the source file is the curated set, so the stage is 1:1 with it.

**2. Describe.** `backend/occupations/descriptions.py` populates the `description` field for each occupation from the bundled BLS SOC 2018 definitions. The definitions ship in `backend/ontology/data/onet_occupation_data.tsv`, sourced from O*NET's Occupation Data release, which redistributes the BLS definitions verbatim on the `.00` rows. The loader prefers the `.00` row for each SOC and falls through to a specialty row only if the parent definition is absent. Anchoring to the federal vocabulary file removes a class of drift the previous implementation suffered: a hand-curated dictionary plus regex-template fallback that drifted from BLS truth on roughly a third of the codes it covered.

**3. Load.** `backend/occupations/load.py` writes the final `occupations.json` into Neo4j. The loader creates or matches `Region` nodes for every distinct region key observed, links each college to its primary COE region via `IN_MARKET`, creates or merges an `Occupation` node per SOC code with `title`, `description`, and `education_level` set on the node, and creates one `DEMANDS` edge per (region, occupation) pair carrying the four regional-metric properties. All writes use `UNWIND`-driven `MERGE` in batches of `BATCH_SIZE = 500`.

A previous version of this stage ran a Gemini Flash skill-assignment step between describe and load, attaching a closed-vocabulary skill set to each occupation via `REQUIRES_SKILL` edges. That step was retired when the bridge between curriculum and labor market moved to the institutional TOP-CIP-SOC crosswalk: occupations are now connected to courses directly through `Course-[:PREPARES_FOR]->Occupation`, materialized from the Chancellor's Office and BLS/NCES crosswalks at course-load time. The skill-assignment LLM call, the unified taxonomy, the per-occupation skill validation, and the retry loop are all gone — the demand side of the graph now depends on no LLM calls at all, and every Course→Occupation pathway claim is institutionally sourced rather than LLM-derived.

## Loading into the graph

The node and edge shape produced by `load.py` is the canonical occupation surface of the graph. It matches the schema defined in [Graph Model → The node types](../architecture/graph-model.md#the-node-types) and [Graph Model → The relationships](../architecture/graph-model.md#the-relationships).

| Structure | Properties | Source |
|---|---|---|
| `Occupation` node | `soc_code`, `title`, `description`, `education_level` | COE identity + BLS SOC 2018 definitions via `descriptions.py` + COE education column |
| `Region` node | `name`, `display_name` | COE region code + `COE_REGION_DISPLAY` in `backend/ontology/regions.py` |
| `DEMANDS` edge (Region → Occupation) | `employment`, `annual_wage`, `growth_rate`, `annual_openings` | Per-region COE demand row |
| `IN_MARKET` edge (College → Region) | — | `COLLEGE_COE_REGION` in `backend/ontology/regions.py` |
| `PREPARES_FOR` edge (Course → Occupation) | `via_top` | Materialized at course-load time from `Course.top_code` via the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks. See [`backend/ontology/prepares_for.py`](../../backend/ontology/prepares_for.py). |

The placement of `education_level` on the `Occupation` node rather than on the `DEMANDS` edge matters and is worth naming explicitly. A SOC code's typical entry-level education is a property of the occupation as a category, not of a particular region's labor market — a Registered Nurse requires a Bachelor's degree whether they work in the Bay Area or in the Central Valley. The four metrics on the `DEMANDS` edge, by contrast, are genuinely regional: employment, wage, growth, and openings vary by the labor market, which is why they live on the edge and not on the node. This split is the operational expression of the product-level claim that "the same SOC code carries different metadata in different regions" — the metadata that varies is on the edge, and the metadata that does not is on the node.
