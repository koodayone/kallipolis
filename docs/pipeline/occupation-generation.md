# Occupation Generation

Occupations are the demand-side anchor of the Kallipolis graph. They are the pipeline's only entity grounded in a single institutional demand authority — the California Community Colleges' Centers of Excellence for Labor Market Research — and they are the only entity where the same SOC code carries different regional demand profiles in different parts of California. This document describes how the stage takes the COE demand feed, restricts it to the occupations the California community college system classifies as CTE, attaches human-readable descriptions from the BLS SOC 2018 vocabulary, and loads the result as `Region`, `Occupation`, and `DEMANDS` structures in the graph.

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

## The CTE scope

Not every occupation in the COE feed belongs in a community college graph. The scope is the set of occupations the California community college system itself classifies as Career Technical Education — the same classification the Strong Workforce Program rests on. Everything outside that classification is excluded.

The inclusion rule is institutional on both sides:

1. **COE tracks regional demand for the SOC** — the row appears in `occupational_demand_coe.csv`.
2. **A PCAH-classified CTE TOP6 code targets the SOC** — the SOC is reachable from at least one TOP6 code in the Chancellor's Office *TOP Codes to Sectors* file via the TOP→CIP→SOC chain, where PCAH is the *Program and Course Approval Handbook* that classifies every TOP6 code into one of the twelve Doing-What-MATTERS / Strong Workforce industry sectors.

The set of CTE-reachable SOCs is computed by `cte_reachable_socs()` in `backend/ontology/crosswalks.py`, which composes three authoritative crosswalks: Chancellor's Office TOP→CIP, NCES CIP→SOC, and PCAH TOP→Sector. The filter is applied in `backend/occupations/generate.py` before `occupations.json` is written, so every occupation the downstream stages operate on is an occupation the graph will actually load. The same PCAH file anchors the employer side of the graph — see [SWP Sector NAICS Composition](./swp-sector-naics.md) for the NAICS-to-sector mapping that the employer pipeline uses, so both sides speak the same sector vocabulary.

An earlier implementation filtered by the BLS "Typical Entry Level Education" field, dropping any SOC outside postsecondary certificate through bachelor's. That rule was retired because BLS's minimum-credential coding is a federal statistical proxy that miscodes California's CTE trades — electricians, welders, plumbers, machinists, roofers, and cement masons all read as "high school diploma" or "no formal credential" in BLS, because their minimum entry bar is a high school diploma plus apprenticeship or on-the-job training. These occupations enter through CTE certificate programs at California community colleges and are central to Strong Workforce partnership work. The PCAH classification captures them directly. The earlier proxy conflated *"requires post-HS academic credentialing"* with *"is a workforce-development occupation the CC system serves"*; the current filter separates them and uses the institutional authority for the second question.

## How the stage runs

The stage runs three sub-steps end to end. The scripts are independent but share `occupations.json` as the handoff format.

**1. Parse and filter.** `generate.py` reads the COE CSV, coerces each row's employment/wage/growth/openings cells into typed values, applies the CTE-scope filter via `cte_reachable_socs()` from `backend/ontology/crosswalks.py`, and pivots rows into per-occupation records.

**2. Describe.** `backend/occupations/descriptions.py` populates the `description` field for each occupation from the bundled BLS SOC 2018 definitions. The definitions ship in `backend/ontology/data/onet_occupation_data.tsv`, sourced from O*NET's Occupation Data release, which redistributes the BLS definitions verbatim on the `.00` rows. The loader prefers the `.00` row for each SOC and falls through to a specialty row only if the parent definition is absent. Anchoring to the federal vocabulary file removes a class of drift the previous implementation suffered: a hand-curated dictionary plus regex-template fallback that drifted from BLS truth on roughly a third of the codes it covered.

**3. Load.** `backend/occupations/load.py` writes the final `occupations.json` into Neo4j. The loader creates or matches `Region` nodes for every distinct region key observed, links each college to its primary COE region via `IN_MARKET`, creates or merges an `Occupation` node per SOC code with `title`, `description`, and `education_level` set on the node, and creates one `DEMANDS` edge per (region, occupation) pair carrying the four regional-metric properties. All writes use `UNWIND`-driven `MERGE` in batches of `BATCH_SIZE = 500`.

A previous version of this stage ran a Gemini Flash skill-assignment step between describe and load, attaching a closed-vocabulary skill set to each occupation via `REQUIRES_SKILL` edges. That step was retired when the bridge between curriculum and labor market moved to the institutional TOP-CIP-SOC crosswalk: occupations are now connected to courses directly through `Course-[:PREPARES_FOR]->Occupation`, materialized from the Chancellor's Office and BLS/NCES crosswalks at course-load time. The skill-assignment LLM call, the unified taxonomy, the per-occupation skill validation, and the retry loop are all gone — the demand side of the graph now depends on no LLM calls at all, and every Course→Occupation pathway claim is institutionally sourced rather than LLM-derived.

## Loading into the graph

The node and edge shape produced by `load.py` is the canonical occupation surface of the graph. It matches the schema defined in [Graph Model → The seven node types](../architecture/graph-model.md#the-seven-node-types) and [Graph Model → The nine relationship pairings](../architecture/graph-model.md#the-nine-relationship-pairings).

| Structure | Properties | Source |
|---|---|---|
| `Occupation` node | `soc_code`, `title`, `description`, `education_level` | COE identity + BLS SOC 2018 definitions via `descriptions.py` + COE education column |
| `Region` node | `name`, `display_name` | COE region code + `COE_REGION_DISPLAY` in `backend/ontology/regions.py` |
| `DEMANDS` edge (Region → Occupation) | `employment`, `annual_wage`, `growth_rate`, `annual_openings` | Per-region COE demand row |
| `IN_MARKET` edge (College → Region) | — | `COLLEGE_COE_REGION` in `backend/ontology/regions.py` |
| `PREPARES_FOR` edge (Course → Occupation) | `via_top` | Materialized at course-load time from `Course.top_code` via the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks. See [`backend/ontology/prepares_for.py`](../../backend/ontology/prepares_for.py). |

The placement of `education_level` on the `Occupation` node rather than on the `DEMANDS` edge matters and is worth naming explicitly. A SOC code's typical entry-level education is a property of the occupation as a category, not of a particular region's labor market — a Registered Nurse requires a Bachelor's degree whether they work in the Bay Area or in the Central Valley. The four metrics on the `DEMANDS` edge, by contrast, are genuinely regional: employment, wage, growth, and openings vary by the labor market, which is why they live on the edge and not on the node. This split is the operational expression of the product-level claim that "the same SOC code carries different metadata in different regions" — the metadata that varies is on the edge, and the metadata that does not is on the node.
