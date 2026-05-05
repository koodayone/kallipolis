# Course Generation

The course generation stage extracts course records from a college's catalog PDF. The output is a set of `Course` nodes per college, each linked to its `Department` and tagged with the institutional TOP6 code that powers the `PREPARES_FOR` bridge to occupations. This document describes what the stage does and what the cached output carries.

## Why the catalog PDF is the source

A college's catalog is the institution's public commitment to teach. It is the only document a college stands behind publicly that enumerates what every course delivers at the unit of one course at a time. Syllabi vary per instructor and term; program requirement tables list codes without content. The catalog carries the descriptive prose, learning outcomes, and course objectives that make a course substantively interpretable.

The cost is that catalogs arrive as PDFs of uneven quality — text-extractable in most cases, image-based in a few, and structured around page layouts rather than field schemas. The extraction stage is what converts that prose into structured records the graph can hold.

## How the stage runs

`backend/courses/scrape_pdf.py` is the single extraction entry point. `scrape_pdf_catalog(pdf_url, college_key)` runs in five conceptual steps.

**1. Download and cache the PDF.** The catalog is fetched once and cached under `backend/pipeline/cache/` keyed by college. Re-runs for the same college skip the download.

**2. Filter to course-description pages.** Every page is text-extracted with `pypdf` and tested against a course-code regex that matches single-word prefixes ("ENGL 1A"), multi-word prefixes ("C S 1A", "MED A 10"), and two-letter suffixes ("CIS 101L"). A page with at least `MIN_CODES_PER_PAGE = 2` regex hits *and* at least two prose lines longer than 80 characters is flagged as a course description page. Program requirement tables, which match the code regex but lack prose, fall out at the second check.

**3. Fall back to full-catalog processing when filtering fails.** If fewer than 10% of pages survive the heuristic — the typical sign of an image-based or atypically encoded PDF — the pipeline processes all pages instead. This keeps coverage non-brittle at the cost of higher token spend on a minority of catalogs.

**4. Chunk and extract via Gemini Flash.** Course pages are grouped into batches of `PAGES_PER_BATCH = 25`, each batch is written to a temporary PDF chunk, and the chunk is sent to `gemini-2.5-flash` with a system instruction that asks for course fields only — code, name, department, units, description, prerequisites, learning outcomes, course objectives, transfer status, GE area, grading, hours. Up to `CONCURRENCY = 5` batches run in parallel. Truncated responses are retried by halving the page range; consecutive 429s are tracked in a shared counter and the whole college aborts once `RATE_LIMIT_ABORT_THRESHOLD = 5` is reached so that a quota-exhausted run fails fast instead of burning wall-clock time.

**5. Deduplicate and cache.** Extracted course dicts are deduplicated by normalized course code — `normalize_course_code` collapses case, whitespace, hyphens, and dots, so "C S 1A", "CS 1A", and "cs-1a" resolve to one entry. The most-populated of each collision wins. The result is written to `{college_key}_enriched.json`, returned to the pipeline as a list of `RawCourse` objects, and loaded into Neo4j by `backend/courses/load.py`.

## How courses bridge to occupations

The pipeline overview previously listed course extraction (stage 1) and skill derivation (stage 2) as separate stages. The skill-derivation stage has been retired: the bridge between curriculum and labor market now runs through the institutional TOP-CIP-SOC crosswalk maintained by the California Community Colleges Chancellor's Office and BLS/NCES, not through an internally-derived skill index.

The mechanism, materialized in [`backend/courses/load.py`](../../backend/courses/load.py) and [`backend/ontology/prepares_for.py`](../../backend/ontology/prepares_for.py):

1. After courses are loaded, each course's `top_code` property is set from the per-college Master Course File via `backend/ontology/mcf_lookup.py`. The MCF is the Chancellor's Office authoritative course-to-TOP6 assignment — one TOP6 per course per college.
2. The TOP6→CIP and CIP→SOC crosswalks compose to a TOP6→{SOC} mapping in `top6_to_soc()` in [`backend/ontology/crosswalks.py`](../../backend/ontology/crosswalks.py).
3. For every (college, course) pair with a `top_code`, the loader writes one `Course-[:PREPARES_FOR {via_top}]->Occupation` edge per SOC the composed mapping yields. Edges to occupations not in the graph (excluded by the institutional CTE filter at occupation load time) are skipped.

Every Course→Occupation pathway claim therefore points back to two named external publications. There is no Gemini call between course extraction and the bridge edge — the bridge is fully institutional and fully deterministic.

## Department canonicalization

Gemini's per-course `department` field has a structural failure mode. Because the PDF is chunked into 25-page batches and each batch is extracted independently, the same subject surfaces as multiple department strings depending on what subject-header context the chunk happened to include — Foothill's catalog produces "Dance", "Dance (DANC)", and "DANC" for the same subject; SBCC's noncredit programs surface under shorter labels than their credit twins. The atlas UI groups by the raw string, so one real subject fragments into multiple adjacent buckets.

The pipeline resolves this by making `department` a derived, deterministic value computed from each course's TOP6 code via the official Chancellor's Office Taxonomy of Programs Manual. The TOP6 lookup is already authoritative (`backend/ontology/mcf_lookup.py` matches each course code against the per-college MIS Master Course File); rolling the TOP6 up to its TOP4 program area and labeling it with the manual's canonical name makes department names institutional, uniform across colleges, and immune to per-college overlay drift. Gemini's `department` field is preserved on the Course node as `catalog_section` for traceability but is not used for grouping.

### The TOP4 name table

The lookup table lives at `backend/ontology/data/top4_names.json` and is parsed once from `cc-top-code-manual.pdf` (7th ed., May 2023). It contains:

- 223 TOP4 → name entries (`"0502"` → `"Accounting"`, `"1004"` → `"Music"`, `"4930"` → `"General Studies"`)
- 24 TOP2 → name entries (`"05"` → `"Business and Management"`) for fallback when a TOP4 has no standalone manual entry

The helper `top_to_department_name(top6)` in `backend/ontology/crosswalks.py` resolves any 6-digit TOP code through this table in two steps: first attempt the TOP4 entry from `top6[:4]`, falling back to the TOP2 entry from `top6[:2]` for the rare TOP4 ranges (like `4930.x`) that the manual treats as a holding bucket without a standalone TOP4 row.

The table is the single authoritative source. There is no per-college curation, no overlay file, and no "Unmapped: X" escape hatch. Courses without a MCF TOP6 — about 5% of catalog-extracted rows, typically real MCF lag for new GE codes — get an empty department and are filtered out of the courses API by the `WHERE c.top_code IS NOT NULL` clause in `backend/courses/api.py`.

### Stage integration

The Neo4j loader at `backend/courses/load.py` reads each enriched course's TOP6 from `lookup_top6_per_course`, resolves the department name through `top_to_department_name`, and writes both `Course.top_code` and `Course.department` in a single MERGE. Department nodes are MERGEd on the resolved name and linked via `College -[:OFFERS]→ Department -[:CONTAINS]→ Course`. The same load-tail cleanup that previously protected against overlay drift remains in place: `CONTAINS` edges whose Department name disagrees with the Course's current `department` are deleted, `OFFERS` edges to empty Departments are deleted, and orphan Department nodes are detach-deleted after each load.

### Catalog-extraction artifact filter

A separate problem the prior overlay system absorbed silently: Gemini's catalog scrape sometimes emits "courses" that are actually credential listings ("Accounting, Associate in Science"), table-of-contents fragments ("10: Welcome"), C-IDs ("C1000"), or Greek-letter visual-duplicate codes ("ΑΝΤΗ 102"). The TOP4 pivot exposed these because they consistently fail to resolve to a TOP6 and thus to a department.

`backend/courses/extraction_filter.py::is_artifact(code, name)` is the deterministic rejection rule. It runs at extraction time inside `backend/courses/scrape_pdf.py` and again as a safety net in `backend/pipeline/run.py` on the cached enriched.json. Categories it rejects: pure-numeric codes (`"104"`), prefix-only codes (`"THEA"`), question-mark fragments, non-ASCII alpha (Greek-letter twins), names containing degree-program markers (`"Associate in Arts"`, `"Skills Competency Award"`, `"Certificate of Achievement"`), C-ID patterns (`"C1000"`, `"Communication C1000"`), and non-CCC institutional prefixes (`"UNR ENG"` for Lassen's Univ. of Nevada-Reno cross-enrollment).

The filter and the audit at `tools/courses-audit/classify_unmapped.py` share the same predicates so what's filtered at load time matches what the audit would report later.

### What this produces

After the pivot, every visible Course at every onboarded college has a department name traceable to a specific row in `cc-top-code-manual.pdf`. The 22 featured colleges have between 47 and 120 distinct TOP4 program names each (SBCC at the high end, Berkeley City at the low end), zero `Unmapped: X` placeholders, and zero off-manual department names in the graph. Cross-college, the same TOP4 code resolves to the same name everywhere — Music at Foothill is the same Department node as Music at SBCC, structurally enforced.

## Provenance and quality signals

Every extraction run writes a sidecar `{college_key}_extraction_meta.json` next to the enriched cache. The sidecar records provenance (extractor name and version, extraction timestamp, PDF URL) and quality metrics (pages processed, batches truncated, batches rate-limited, missing-description and missing-department counts).

The sidecar is a sidecar, not a wrapper around the enriched cache, because `backend/pipeline/run.py` reads the enriched cache as a JSON list and wrapping it would break the contract.

## Known sharp edges

Two operational caveats are worth knowing.

**PDF text-layer variance.** Community college catalogs are produced from Word or InDesign and are usually text-extractable, but a minority use image-based rendering or nonstandard encodings. Page filtering fails silently on those catalogs; the 10% fallback is what catches them. Checking the `course_page_fraction` field in the extraction sidecar is the operational discipline that distinguishes "fallback fired correctly" from "catalog genuinely has few courses."

**Program-table contamination.** The system prompt tells the model to skip program requirement tables and extract only from course description sections, but there is no programmatic check. A program-table entry that shares a formatting variant with a real course can produce a ghost duplicate that the code-normalization step collapses in most cases but not all. Spot-checking the `raw_courses_before_dedup` vs. `courses_extracted` fields in the sidecar is the cheapest way to detect when dedup is doing unexpectedly heavy work.

## What the output represents

The loaded `Course` node is a structured representation of the institution's published commitment to teach, not a verbatim transcription of the catalog. The prose has been parsed into fields, and the code has been normalized for joinability. A coordinator looking at the curriculum side of the [graph](../architecture/graph-model.md) is looking at an extracted-and-structured view of the catalog, with each course tagged with the institutional TOP6 code that drives its `PREPARES_FOR` edges to occupations.
