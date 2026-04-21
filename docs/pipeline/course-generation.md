# Course Generation

The course generation stage extracts course records and the skills each course develops from a college's catalog PDF. The output is a set of `Course` nodes per college, each linked to its `Department` and to the skills it develops through `DEVELOPS` edges. This document describes what the stage does, how it derives skills, and what the cached output carries.

## Why the catalog PDF is the source

A college's catalog is the institution's public commitment to teach. It is the only document a college stands behind publicly that enumerates what every course delivers at the unit of one course at a time. Syllabi vary per instructor and term; program requirement tables list codes without content. The catalog carries the descriptive prose, learning outcomes, and course objectives that make a course substantively interpretable against the unified skill taxonomy.

The cost is that catalogs arrive as PDFs of uneven quality — text-extractable in most cases, image-based in a few, and structured around page layouts rather than field schemas. The extraction stage is what converts that prose into structured records the graph can hold.

## How the stage runs

`backend/courses/scrape_pdf.py` is the single extraction entry point. `scrape_pdf_catalog(pdf_url, college_key)` runs in five conceptual steps.

**1. Download and cache the PDF.** The catalog is fetched once and cached under `backend/pipeline/cache/` keyed by college. Re-runs for the same college skip the download.

**2. Filter to course-description pages.** Every page is text-extracted with `pypdf` and tested against a course-code regex that matches single-word prefixes ("ENGL 1A"), multi-word prefixes ("C S 1A", "MED A 10"), and two-letter suffixes ("CIS 101L"). A page with at least `MIN_CODES_PER_PAGE = 2` regex hits *and* at least two prose lines longer than 80 characters is flagged as a course description page. Program requirement tables, which match the code regex but lack prose, fall out at the second check.

**3. Fall back to full-catalog processing when filtering fails.** If fewer than 10% of pages survive the heuristic — the typical sign of an image-based or atypically encoded PDF — the pipeline processes all pages instead. This keeps coverage non-brittle at the cost of higher token spend on a minority of catalogs.

**4. Chunk and extract via Gemini Flash.** Course pages are grouped into batches of `PAGES_PER_BATCH = 25`, each batch is written to a temporary PDF chunk, and the chunk is sent to `gemini-2.5-flash` with a system instruction that asks for both course fields *and* `skill_mappings` in a single call. Up to `CONCURRENCY = 5` batches run in parallel. Truncated responses are retried by halving the page range; consecutive 429s are tracked in a shared counter and the whole college aborts once `RATE_LIMIT_ABORT_THRESHOLD = 5` is reached so that a quota-exhausted run fails fast instead of burning wall-clock time.

**5. Deduplicate and cache.** Extracted course dicts are deduplicated by normalized course code — `normalize_course_code` collapses case, whitespace, hyphens, and dots, so "C S 1A", "CS 1A", and "cs-1a" resolve to one entry. The most-populated of each collision wins. The result is written to `{college_key}_enriched.json`, returned to the pipeline as a list of `RawCourse` objects, and loaded into Neo4j by `backend/courses/load.py`.

## How skills are derived

The pipeline overview lists course extraction (stage 1) and skill enrichment (stage 2) as separate stages. In this implementation they are a single Gemini call. The system instruction interpolates the unified taxonomy at runtime from `backend/ontology/skills.py`, so there is no static prompt file that can drift from the live vocabulary.

The model is instructed to select only from the taxonomy and not to invent new skill names. The final guard is in the loader: `backend/courses/load.py` validates each `skill_mappings` entry against `UNIFIED_TAXONOMY` before writing a `DEVELOPS` edge, and any off-taxonomy term is dropped with a warning. This is what makes the closed-vocabulary claim in the [courses product document](../product/courses.md) operationally true — even when the model deviates, the graph sees only validated skills.

The skill-count target is at least six per course. In practice the observed average across loaded colleges sits around 4.5–4.8 skills per course, and the target is aspirational rather than enforced. This is the methodological pressure point the product document names as the place where the methodology has room to evolve.

## Department canonicalization

Gemini's per-course `department` field has a structural failure mode. Because the PDF is chunked into 25-page batches and each batch is extracted independently, the same subject surfaces as multiple department strings depending on what subject-header context the chunk happened to include. Foothill's catalog produces all of "Dance", "Dance (DANC)", and "DANC" for the same subject; STAT courses surface under "Mathematics (MATH)"; several colleges' English, Political Science, and Psychology courses pick up unrelated GE-category labels. The atlas UI groups by the raw string, so one real subject fragments into two or three adjacent buckets.

The pipeline resolves this by making `department` a derived, deterministic, human-readable value computed from the course code's prefix rather than trusted from Gemini. The course code is reliable (Gemini produces clean codes, validated in the course-extraction audit), the prefix identifies the subject, and a committed prefix-to-name mapping supplies the canonical display name. Gemini's `department` output is ignored at load time.

### The mapping

The mapping lives at `backend/courses/department_mapping/` and has two layers that merge at resolve time:

- `backend/courses/department_mapping/base.json` holds prefixes with stable names across California community college catalogs (`MATH → Mathematics`, `ENGL → English`, `BIOL → Biology`). This file is lean — only prefixes whose naming convention is genuinely universal.
- `backend/courses/department_mapping/overlays/foothill.json` and its siblings hold per-college additions and overrides. College-specific programs (Foothill's `APSM → Apprenticeship: Sheet Metal`) and local naming variants live in each college's overlay file. Resolution is base ∪ overlay with overlay winning on conflict.

Mapping files are validated at load time by `backend/courses/department_mapping/__init__.py`. Invariants the resolver enforces:

| Invariant | Rationale |
|---|---|
| Every value is a non-empty string | Rejects malformed entries |
| No value equals its key | A bare code like `"STAT"` as a display label is a UI failure |
| No value ends with a parenthesized all-caps code | Rejects the `"Dance (DANC)"` fragmentation pattern at the source |
| No value is shorter than three characters | Guards against accidental truncation to initials |
| Two prefixes mapping to the same name must be whitelisted in `_meta.allowed_collisions` | Intentional shared names (e.g., `POLI` and `POLS` both resolving to `"Political Science"` for old and new CCCN numbering) are explicit; accidental collisions fail loudly |

### Seeding and promotion

`tools/courses-audit/seed_department_mapping.py` produces a candidate overlay for a college that does not yet have one. The seeder scans the catalog PDF with pypdf for every parenthesized-prefix occurrence (`(DANC)`, `(V T)`, and so on), collects a short context snippet around each match, and sends the aggregated evidence to `claude-sonnet-4-6` with a prompt that asks for the canonical California community college department name per prefix. One API call per college, typically under 15k input tokens, bounded at roughly $0.01 per college. The output is written to a sibling `.proposed.json` file next to the eventual overlay location, meant for operator review before promotion.

The division of labor is deliberate: pypdf gathers raw evidence without committing to any single catalog layout, and the LLM distills the messy observations into canonical names using the catalog's own wording. Course titles are a secondary backup signal used only when PDF text is sparse; they are never the primary source, because names inferred from titles would be derived rather than authoritative.

`tools/courses-audit/promote_overlays.py` promotes reviewed proposals to committed overlays. It re-validates the proposal against the resolver's invariants, detects any legitimate shared-name collisions and auto-adds them to `_meta.allowed_collisions`, stamps `_meta.last_reviewed`, and renames the proposal file to its final committed form. Proposals that fail invariants are reported and not promoted — those are the ones that need human inspection.

### Stage integration

Canonicalization runs between skill enrichment and the Neo4j load. `backend/pipeline/run.py` calls `_canonicalize_departments` on the enriched course list: each course's prefix is extracted from its code, looked up in the resolved mapping, and the `department` field is rewritten to the canonical value. Courses whose codes are malformed and unparseable pass through with a surface cleanup — any trailing parenthesized-code suffix on the Gemini-emitted department string is stripped so a single unparseable course does not create a singleton UI bucket with a fragmented label.

The Neo4j loader at `backend/courses/load.py` then creates Department nodes MERGEd on the canonical name and runs three cleanup Cypher queries after the load: `CONTAINS` edges where the Department name disagrees with the Course's current `department` property are deleted, `OFFERS` edges from the College to Departments that no longer hold any of its courses are deleted, and orphan Department nodes with no outbound `CONTAINS` edges are detached and deleted. This makes the canonicalization converge cleanly even when a college was previously loaded under fragmented labels.

The onboarding workflow at `.claude/skills/onboard-college/SKILL.md` adds a preflight check that requires the overlay file to exist before the pipeline can progress past Stage 2, preventing accidental loads that would propagate fragmented department data into the graph.

### What this produces

After canonicalization, the atlas UI renders a single clean department bucket per subject. Across the eight featured colleges, the graph holds 611 canonical Department nodes down from roughly 700 fragmented strings Gemini originally emitted. Soft-failure coverage is high: approximately 0.2% of courses across the featured colleges have codes that extract-prefix cannot parse (catalog-specific annotation markers, slash-alternate numberings, upstream Gemini glitches), and those courses pass through with their lightly-cleaned Gemini labels rather than being dropped from the graph.

The CI test `test_every_prefix_resolves` in `backend/courses/test_department_mapping.py` enforces the human-readable invariant across every onboarded college on every run, so a prefix introduced by a catalog update without a mapping entry fails CI rather than silently producing a `"Unmapped: PREFIX"` placeholder in production.

## Provenance and quality signals

Every extraction run writes a sidecar `{college_key}_extraction_meta.json` next to the enriched cache. The sidecar records provenance (extractor name and version, extraction timestamp, PDF URL, taxonomy hash at extraction time) and quality metrics (pages processed, batches truncated, batches rate-limited, average and distribution of skill counts, unique taxonomy skills used, missing-description and missing-department counts).

The sidecar is a sidecar, not a wrapper around the enriched cache, because `backend/pipeline/run.py` reads the enriched cache as a JSON list and wrapping it would break the contract.

The taxonomy hash is the load-bearing field. An enriched file whose taxonomy hash no longer matches the current vocabulary was extracted against a stale vocabulary and should be regenerated before being loaded, not silently reused. This is the mechanism by which taxonomy evolution invalidates old caches.

## Known sharp edges

Two operational caveats are worth knowing.

**PDF text-layer variance.** Community college catalogs are produced from Word or InDesign and are usually text-extractable, but a minority use image-based rendering or nonstandard encodings. Page filtering fails silently on those catalogs; the 10% fallback is what catches them. Checking the `course_page_fraction` field in the extraction sidecar is the operational discipline that distinguishes "fallback fired correctly" from "catalog genuinely has few courses."

**Program-table contamination.** The system prompt tells the model to skip program requirement tables and extract only from course description sections, but there is no programmatic check. A program-table entry that shares a formatting variant with a real course can produce a ghost duplicate that the code-normalization step collapses in most cases but not all. Spot-checking the `raw_courses_before_dedup` vs. `courses_extracted` fields in the sidecar is the cheapest way to detect when dedup is doing unexpectedly heavy work.

## What the output represents

The loaded `Course` node is a structured representation of the institution's published commitment to teach, not a verbatim transcription of the catalog. The prose has been parsed into fields, the skills have been derived against a controlled vocabulary, and the code has been normalized for joinability. A coordinator looking at the curriculum side of the [graph](../architecture/graph-model.md) is looking at an extracted-and-structured view of the catalog, and the extraction sidecar is the evidence that the view is recognizable as faithful at the aggregate level.
