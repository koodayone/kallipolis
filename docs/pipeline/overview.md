# Pipeline: Overview

The pipeline is the mechanism by which the Kallipolis ontology comes into being. It is a set of stages that take raw institutional sources — college catalog PDFs, COE labor market data, EDD employer records — and transform them into the Neo4j graph that the product reads from. This document describes the pipeline at the level a reader needs to hold its shape in their head: what the stages are, what each stage produces, and how they fit together.

## What the pipeline does

The pipeline's job is to populate the [graph model](../architecture/graph-model.md) from authoritative external sources. Each stage takes input from a specific source, applies transformation work (some of which is LLM-mediated), and produces nodes and relationships in the Neo4j graph. The pipeline is what makes the data authority principle operational — every node in the graph traces back, through one of these stages, to a source the [data authorities document](../domain/data-authorities.md) names.

The pipeline is run per college (for the curriculum side) and per region (for the industry side). Both sides converge in the same graph because the institutional TOP-CIP-SOC crosswalk maintained by the Chancellor's Office and BLS/NCES gives them a shared bridge, materialized as `Course-[:PREPARES_FOR]->Occupation` edges.

## The stages

The pipeline has five stages, each one corresponding to a specific transformation from source to graph.

| Stage | Input | Transformation | Output |
|---|---|---|---|
| **1. Course extraction** | College catalog PDFs | PDF parsing + LLM-mediated extraction | `RawCourse` records per college |
| **2. Curriculum loading** | Enriched courses + Master Course File + TOP-CIP and CIP-SOC crosswalks | Direct write to Neo4j + crosswalk-driven `PREPARES_FOR` materialization | College, Department, Course nodes plus `Course-[:PREPARES_FOR]->Occupation` edges |
| **3. Student generation** | Enriched courses + per-college calibration data | Synthetic generation against DataMart enrollment distributions | Student nodes with `ENROLLED_IN` edges |
| **4. Industry data** | COE labor market data, EDD employer records | Parsing, LLM-mediated employer cleanup | Region, Occupation, Employer nodes and their relationships |
| **5. Partnership alignment** | The loaded graph (curriculum + industry + students) | Deterministic traversal that derives per-employer alignment metrics | `PARTNERSHIP_ALIGNMENT` edges from each College to the employers in its region |

Stages 1–3 run per college and produce the curriculum side of the graph. Stage 4 runs per region and produces the industry side. Stage 5 runs per college but depends on both sides being loaded, so it comes last; it is the only stage that writes a derived analytical edge rather than loading source data. The two halves of the graph are independent until they meet at occupations through the institutional TOP-CIP-SOC crosswalk — and stage 5 is where the partnership-relevant slice of that bridge gets precomputed for the partnership landscape view.

## The two halves of the pipeline

The pipeline divides naturally into two halves, each populating one side of the [graph model](../architecture/graph-model.md).

### Curriculum-side pipeline

The curriculum-side pipeline takes a college from a catalog PDF to a populated set of courses, departments, and synthetic students. Stages 1, 2, and 3 run for each college.

**Stage 1 (Course extraction)** is a Gemini call per page-range chunk. The catalog PDF is downloaded, course-bearing pages are filtered by a course-code regex, and chunks are sent to `gemini-2.5-flash` with a system prompt that asks for the structured course fields only — no skill derivation. Each response carries the structured course fields (code, name, department, units, description, prerequisites, learning outcomes, course objectives, transfer status, GE area, grading, hours). Output is cached as `{college}_enriched.json` with a provenance sidecar at `{college}_extraction_meta.json`. For the full treatment of the extraction methodology and the sidecar schema, see [Course Generation](./course-generation.md).

At load time, each course's `department` field is derived deterministically from its TOP6 code via the Chancellor's Office Taxonomy of Programs Manual (parsed once into `backend/ontology/data/top4_names.json`). A separate extraction filter at `backend/courses/extraction_filter.py` rejects catalog-extraction artifacts — credential listings, page fragments, C-IDs, non-CCC prefixes — before they enter Neo4j. The detailed treatment is in [Course Generation](./course-generation.md).

**Stage 2 (Curriculum loading)** writes the enriched courses into Neo4j and materializes the `PREPARES_FOR` bridge edges. The College node is created or matched, Departments are derived from the course department fields, Course nodes are written with all properties, and `top_code` is set on each Course from the Master Course File. The loader then composes the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks via `top6_to_soc()` in [`backend/ontology/crosswalks.py`](../../backend/ontology/crosswalks.py) and writes one `Course-[:PREPARES_FOR {via_top}]->Occupation` edge per (course, SOC) pair the composed mapping yields. This is direct database writing — no LLM involvement.

**Stage 3 (Student generation)** produces a synthetic student population for the college. The methodology uses per-college calibration data derived from DataMart 4-digit TOP code grade distributions and the college's own published institutional data (enrollment, full-time ratio, retention rate). The algorithm generates students, assigns each one a primary 4-digit TOP code, distributes their course-taking across the relevant pool, and samples grades from the empirical TOP-code grade distributions. The output is `Student` nodes with `ENROLLED_IN` edges.

For the full treatment of the synthetic student methodology, see [Student Generation](./student-generation.md).

### Industry-side pipeline

The industry-side pipeline runs once per region and populates Region, Occupation, and Employer nodes with their relationships. It is structurally distinct from the curriculum-side pipeline because the data sources are different and the operations happen at the region level rather than the college level.

**Occupation loading** parses Centers of Excellence occupational demand data across nine COE regions plus statewide, restricts it to the occupations the Chancellor's Office classifies as Career Technical Education (via the TOP→CIP→SOC crosswalk and the PCAH sector file), attaches descriptions, and writes `Region`, `Occupation`, `DEMANDS`, and `IN_MARKET` structures into Neo4j. COE is the sole source for demand metrics; an earlier OEWS-based pipeline has been retired. The full treatment is in [Occupation Generation](./occupation-generation.md).

**Employer loading** is the most operationally subtle stage in the pipeline because employers are sourced at the county level from EDD records, scoped per college, and merged into a region-shared employer pool with deliberate cleanup. The full treatment is in [Employer Generation](./employer-generation.md).

For the industry side overall, occupations and employers together populate the demand layer of the graph. The bridge to the curriculum side runs through the `PREPARES_FOR` edges materialized in stage 2.

## Orchestration

The operator-facing entry point for running the full pipeline end-to-end for a new college is the `onboard-college` Claude Code skill at `.claude/skills/onboard-college/SKILL.md`. The skill wraps the scripts described below into a five-stage sequence — curriculum extraction + load, student generation, employer generation, employer validation (via the `validate-employers` skill), employer load, and partnership alignment precompute — with a preflight verification pass and a final graph-state check. Running "onboard College X" inside Claude Code executes the full sequence with cache-aware re-run detection and no operator knowledge of the intermediate commands. The raw Python scripts below remain supported for testing and partial re-runs.

The pipeline is orchestrated by two scripts depending on the scope of the operation.

`backend/pipeline/run.py` runs the curriculum-side stages (1–3) for one college at a time. It supports incremental execution: stages can be skipped if their cached output exists, and students can be generated without re-running extraction. This is the script used during development and when adding new colleges to the system. Because `run.py` is scoped to one college's curriculum, it does not run stage 4 (industry data, which is region-scoped) or stage 5 (partnership alignment, which depends on both sides being loaded).

`backend/pipeline/reload.py` runs a full graph rebuild for an entire region. It clears the existing graph, then runs stages 2 (curriculum loading), 4 (industry data), 3 (student generation), and 5 (partnership alignment precompute) for every college in the region. This is the script used when the graph schema changes, when a calibration methodology is updated, or when a region's data needs to be regenerated from scratch. It is also the only script that produces `PARTNERSHIP_ALIGNMENT` edges, which means partnership landscape queries return empty until `reload.py` has run against the target database.

The two scripts are complementary. `run.py` is for incremental curriculum work; `reload.py` is for system-wide rebuilds including industry and partnership alignment.

## Where the LLM-mediated work happens

Two stages use LLM calls — the two that derive structure from unstructured or semi-structured sources. Stages 2, 3, and 5 are deterministic and write directly to Neo4j. All pipeline LLM calls go through Gemini; Claude is reserved for request-time work (see [AI Integration](../architecture/ai-integration.md) for the full split).

| Stage | LLM operation | Constraint |
|---|---|---|
| 1. Course extraction | Structured extraction from PDF pages | Output schema enforces course shape |
| 4. Industry: employer cleanup | Name normalization, sector classification, occupation assignment | Validated against existing region's occupation set |

The pipeline used to carry two additional LLM-mediated stages — skill derivation on the curriculum side and skill assignment on the industry side — that have been retired. The bridge between curriculum and labor market now runs through the institutional TOP-CIP-SOC crosswalk, not through an LLM-derived skill index. In every remaining LLM call, the model is operating against a constrained context — either a structured output schema (stage 1) or an institutional reference set (stage 4).

## What this section does not yet cover

This overview is the entry point for the pipeline section. Four sub-documents fill in the substantive detail:

- [Course Generation](./course-generation.md) — the PDF extraction methodology, the institutional `PREPARES_FOR` materialization at load time, the extraction_meta sidecar, and the known sharp edges around PDF text-layer variance and program-table contamination
- [Student Generation](./student-generation.md) — the synthetic methodology, the calibration data, the per-college TOP-code distribution algorithm, and what the generated population is and is not
- [Occupation Generation](./occupation-generation.md) — the COE demand feed, the institutional CTE scope filter (PCAH TOP→CIP→SOC), and why `education_level` lives on the `Occupation` node rather than on the `DEMANDS` edge
- [Employer Generation](./employer-generation.md) — the EDD scraping, the county-to-region crosswalk, the merge semantics, and the pass-through model that lets multiple colleges share an employer pool

Stages 2 and 5 (curriculum loading and partnership alignment) are described at the right level here and do not warrant separate documents at the current stage.
