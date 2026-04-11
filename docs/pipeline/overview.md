# Pipeline: Overview

The pipeline is the mechanism by which the Kallipolis ontology comes into being. It is a set of stages that take raw institutional sources — college catalog PDFs, COE labor market data, EDD employer records — and transform them into the Neo4j graph that the product reads from. This document describes the pipeline at the level a reader needs to hold its shape in their head: what the stages are, what each stage produces, and how they fit together.

## What the pipeline does

The pipeline's job is to populate the [graph model](../architecture/graph-model.md) from authoritative external sources. Each stage takes input from a specific source, applies transformation work (some of which is LLM-mediated), and produces nodes and relationships in the Neo4j graph. The pipeline is what makes the data authority principle operational — every node in the graph traces back, through one of these stages, to a source the [data authorities document](../domain/data-authorities.md) names.

The pipeline is run per college (for the curriculum side) and per region (for the industry side). Both sides converge in the same graph because the unified skills taxonomy gives them a shared vocabulary, and the resulting graph is what the [system overview](../architecture/system-overview.md) describes as the center of the architecture.

## The stages

The pipeline has six stages, each one corresponding to a specific transformation from source to graph.

| Stage | Input | Transformation | Output |
|---|---|---|---|
| **1. Course extraction** | College catalog PDFs | PDF parsing + LLM-mediated extraction | `RawCourse` records per college |
| **2. Skill enrichment** | Raw courses + unified skill taxonomy | LLM-mediated mapping against the controlled vocabulary | Enriched courses with `skill_mappings` |
| **3. Curriculum loading** | Enriched courses | Direct write to Neo4j | College, Department, Course, Skill nodes and their relationships |
| **4. Student generation** | Enriched courses + per-college calibration data | Synthetic generation against DataMart enrollment distributions | Student nodes with `ENROLLED_IN` and `HAS_SKILL` edges |
| **5. Industry data** | EDD OEWS, COE labor market data, EDD employer records | Parsing, LLM cleanup, controlled-vocabulary skill assignment | Region, Occupation, Employer nodes and their relationships |
| **6. Partnership alignment** | The loaded graph (curriculum + industry + students) | Deterministic traversal that derives per-employer alignment metrics | `PARTNERSHIP_ALIGNMENT` edges from each College to the employers in its region |

Stages 1–4 run per college and produce the curriculum side of the graph. Stage 5 runs per region and produces the industry side. Stage 6 runs per college but depends on both sides being loaded, so it comes last; it is the only stage that writes a derived analytical edge rather than loading source data. The two halves of the graph are independent until they meet at the skill nodes, where the unified taxonomy allows curriculum-side and industry-side skill claims to be matched against each other — and stage 6 is where that match gets precomputed for the partnership landscape view.

## The two halves of the pipeline

The pipeline divides naturally into two halves, each populating one side of the [graph model](../architecture/graph-model.md).

### Curriculum-side pipeline

The curriculum-side pipeline takes a college from a catalog PDF to a populated set of courses, departments, and synthetic students. Stages 1, 2, 3, and 4 run for each college.

**Stage 1 (Course extraction)** uses Gemini to extract structured course data from the college's catalog PDF. The PDF is downloaded, course-bearing pages are detected by regex on course code patterns, and pages are batched in groups of 25 for the model to process. Each batch produces structured course records — code, title, department, units, description, learning outcomes, course objectives, transfer status. Output is cached as `{college}_raw.json`.

**Stage 2 (Skill enrichment)** sends the extracted courses back through Gemini, this time with the unified skill taxonomy as a controlled vocabulary. Each course gets 3–6 skills assigned from the taxonomy, with the model constrained to prefer existing terms and only introduce new ones when the course teaches something genuinely uncovered. Output is cached as `{college}_enriched.json`.

**Stage 3 (Curriculum loading)** writes the enriched courses into Neo4j. The College node is created or matched, Departments are derived from the course department fields, Course nodes are written with all properties, and `Course → DEVELOPS → Skill` edges are created against the (already-existing or newly-created) Skill nodes. This is direct database writing — no LLM involvement.

**Stage 4 (Student generation)** produces a synthetic student population for the college. The methodology uses per-college calibration data derived from DataMart 4-digit TOP code grade distributions and the college's own published institutional data (enrollment, full-time ratio, retention rate). The algorithm generates students, assigns each one a primary 4-digit TOP code, distributes their course-taking across the relevant pool, samples grades from the empirical TOP-code grade distributions, and materializes `HAS_SKILL` edges from completed courses. The output is `Student` nodes with `ENROLLED_IN` and `HAS_SKILL` edges.

For the full treatment of the synthetic student methodology, see [Student Generation](./student-generation.md).

### Industry-side pipeline

The industry-side pipeline runs once per region and populates Region, Occupation, and Employer nodes with their relationships. It is structurally distinct from the curriculum-side pipeline because the data sources are different and the operations happen at the region level rather than the college level.

**Occupation loading** parses Centers of Excellence occupational demand data at `backend/occupations/generate.py`, covering ~800 SOC codes across nine COE regions plus statewide and filtering to the community-college workforce-development band before writing `occupations.json`. The loader at `backend/occupations/load.py` then writes Region and Occupation nodes with `DEMANDS` edges that carry regional employment, wage, growth, and openings data. Occupations are enriched with skill assignments via a Gemini call constrained to the existing skill taxonomy, producing `REQUIRES_SKILL` edges. COE is the sole data source for the occupations domain; an earlier OEWS-based pipeline has been retired.

**Employer loading** is the most operationally subtle stage in the pipeline because employers are sourced at the county level from EDD records, scoped per college, and merged into a region-shared employer pool with deliberate cleanup. The full treatment is in [Employer Generation](./employer-generation.md).

For the industry side overall, occupations and employers together populate the demand layer of the graph, and the skill assignments connect them to the same taxonomy the curriculum side uses.

### Partnership alignment precompute

After both sides of the graph are loaded, stage 6 traverses the college-region-employer-occupation-skill-course chain to derive per-employer alignment metrics for each college and writes them onto a `PARTNERSHIP_ALIGNMENT` edge from the College node to each relevant Employer node. The edge carries seven properties (`alignment_score`, `gap_count`, `aligned_skills`, `gap_skills`, `top_occupation`, `top_wage`, `pipeline_size`) and exists so that the [partnership landscape endpoint](../architecture/api-reference.md) can return 500+ employers in under a second by reading precomputed properties rather than re-traversing the graph on each request.

The logic lives in `backend/partnerships/compute.py` and is deterministic — no LLM involvement. Stale edges are cleared per-college before recomputation so that employers removed from a region do not leave dangling alignments. For the edge schema, see [Graph Model → Precomputed analytical edge](../architecture/graph-model.md#the-precomputed-analytical-edge).

## Orchestration

The pipeline is orchestrated by two scripts depending on the scope of the operation.

`backend/pipeline/run.py` runs the curriculum-side stages (1–4) for one college at a time. It supports incremental execution: stages can be skipped if their cached output exists, students can be generated without re-running extraction, and skill enrichment can be skipped for a scrape-only run. This is the script used during development and when adding new colleges to the system. Because `run.py` is scoped to one college's curriculum, it does not run stage 5 (industry data, which is region-scoped) or stage 6 (partnership alignment, which depends on both sides being loaded).

`backend/pipeline/reload.py` runs a full graph rebuild for an entire region. It clears the existing graph, then runs stages 3 (curriculum loading), 5 (industry data), 4 (student generation), and 6 (partnership alignment precompute) for every college in the region. This is the script used when the graph schema changes, when a calibration methodology is updated, or when a region's data needs to be regenerated from scratch. It is also the only script that produces `PARTNERSHIP_ALIGNMENT` edges, which means partnership landscape queries return empty until `reload.py` has run against the target database.

The two scripts are complementary. `run.py` is for incremental curriculum work; `reload.py` is for system-wide rebuilds including industry and partnership alignment.

## Where the LLM-mediated work happens

Three stages use LLM calls — the three that derive structure from unstructured or semi-structured sources. Stages 3, 4, and 6 are deterministic and write directly to Neo4j. All pipeline LLM calls go through Gemini; Claude is reserved for request-time work (see [AI Integration](../architecture/ai-integration.md) for the full split).

| Stage | LLM operation | Constraint |
|---|---|---|
| 1. Course extraction | Structured extraction from PDF pages | Output schema enforces course shape |
| 2. Skill enrichment | Skill assignment from controlled vocabulary | Prefer existing taxonomy terms; new terms only when justified |
| 5. Industry: occupation skills | Skill assignment from controlled vocabulary | Same as stage 2 |
| 5. Industry: employer cleanup | Name normalization, sector classification, occupation assignment | Validated against existing region's occupation set |

In every case, the LLM is operating against a constrained context — either a structured output schema (stage 1) or a controlled vocabulary that the model can only select from (stages 2 and 5). This is what makes the LLM-mediated work principled and improvable, in the same register the [skills taxonomy product document](../product/the-skills-taxonomy.md) describes.

## What this section does not yet cover

This overview is the entry point for the pipeline section. Two sub-documents fill in the substantive detail:

- [Student Generation](./student-generation.md) — the synthetic methodology, the calibration data, the per-college TOP-code distribution algorithm, and what the generated population is and is not
- [Employer Generation](./employer-generation.md) — the EDD scraping, the county-to-region crosswalk, the merge semantics, and the pass-through model that lets multiple colleges share an employer pool

The other stages — course extraction, skill enrichment, curriculum loading, occupation loading — are described at the right level here and do not warrant separate documents at the current stage. If they become operationally complex enough to require their own treatment later, they can be added.
