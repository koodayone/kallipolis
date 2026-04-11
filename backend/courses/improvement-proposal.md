# Courses pipeline — state, evaluation, and improvement proposal

*Scope: `backend/courses/`. Analysis only — no code changes in this pass.*

## 1. Current state

### 1.1 Files and what they do

| File | LOC | Role | Wired into pipeline? |
|---|---|---|---|
| `scrape.py` | 382 | CourseLeaf HTML scraper; stdlib `HTMLParser` against `/course-outlines/` index + per-course COR pages. Exports `RawCourse` dataclass and `scrape_catalog()`. | **No.** `RawCourse` is reused as the shared dataclass, but `scrape_catalog()` itself is not called by `pipeline/run.py`. |
| `scrape_curricunet.py` | 521 | CurricUNET/Acadea scraper. Discovers `reportId`, binary-searches the entity ID range, HEAD-probes every ID, fetches and parses each COR. | **No.** Not imported anywhere except its own docstring example. |
| `scrape_pdf.py` | 488 | **The active stage-1+2 codepath.** Downloads the catalog PDF, filters "course" pages by regex, splits into page-range PDF chunks, uploads each chunk to Gemini 2.5 Flash, asks for courses **and** skills in one call, retries truncated chunks by halving, deduplicates, writes `{college}_enriched.json`. | **Yes.** `pipeline/run.py` imports `scrape_pdf_catalog`. |
| `extract.py` | 487 | A **second, parallel** Gemini extraction codepath: pre-extracts page text with `pypdf`, filters course pages, chunks into text-only prompts, sends to Gemini, validates skills against `ontology.skills.UNIFIED_TAXONOMY`, cross-references the MCF to stamp `top_code`/`top4`, writes a `{college}_coverage.json` report. Has its own CLI. | **No.** Not invoked by `pipeline/run.py`. Was run historically — 29 of the 40 `_enriched.json` files in `pipeline/cache/` have a matching `_coverage.json`, which only `extract.py` writes. |
| `load.py` | 197 | Stage-3 Neo4j loader. Idempotent MERGE on `(code, college)`, creates Department and Skill nodes, wires `OFFERS`/`CONTAINS`/`DEVELOPS`. Drops off-taxonomy skills at write time with a warning. | Yes. |
| `api.py` | 125 | FastAPI routes (college, departments, courses, NL query). | Yes. |
| `query.py` | 117 | NL→Cypher translation via `llm/query_engine.py`, with a tight schema/rules prompt. | Yes. |
| `models.py` | 38 | Pydantic response schemas. | Yes. |

There are **zero unit tests** in `backend/courses/`. `cd backend && python3 -m pytest courses/` collects 0 items.

### 1.2 Two-implementation confusion

`scrape_pdf.py` and `extract.py` are two different solutions to the same problem, and both write to the same cache file (`{college}_enriched.json`). The cache directory contains 40 `_enriched.json` files and 29 `_coverage.json` files — so some colleges have been extracted by each pipeline at different times, and there is no provenance field on the cached JSON that says which one produced it. The `from_cache` path in `pipeline/run.py` cannot tell them apart.

The two paths differ substantively:

| Dimension | `scrape_pdf.py` (active) | `extract.py` (dead but reachable via CLI) |
|---|---|---|
| Gemini input | Uploads **PDF chunks** via `client.files.upload` | Sends **pypdf-extracted text** inline in the prompt |
| Page filter regex | `\b[A-Z]{2,6}\s+\d{1,4}[A-Z]?\b` | `\b[A-Z][A-Z .]{1,8}\s*\d{1,4}[A-Z]{0,2}\b` |
| Skill taxonomy injection | Interpolates `TAXONOMY_LIST` into system prompt at call time — stays in sync with `ontology/skills.py` | Loads `pipeline/extraction_prompt.txt`, which contains the taxonomy as **static frozen text** — drifts silently when `ontology/skills.py` changes |
| MCF cross-reference | None — courses never get `top_code`/`top4` stamped | Loads per-college MCF CSV and backfills `top_code`/`top4`/`units` |
| Coverage report | None | Writes `{college}_coverage.json` with page counts, chunk failures, taxonomy/off-taxonomy counts |
| Dependency direction | Correct: imports `ontology.skills` only | **Violates README**: imports `pipeline.mcf_key_map` (features must not import from `pipeline/`) |
| Path portability | Portable | Hardcoded absolute path: `MCF_DIR = Path("/Users/dayonekoo/Desktop/cc_dataset/mastercoursefiles")` — won't work on any other machine, and duplicates the canonical location under `ontology/mastercoursefiles/` referenced in `backend/README.md` |
| Concurrency | `CONCURRENCY=5`, `PAGES_PER_BATCH=25` | `CONCURRENCY=10`, `PAGES_PER_CHUNK=10`, `MAX_CHARS_PER_CHUNK=30000` |
| Truncation handling | Retries truncated chunks by halving | Returns `[]` and logs |

Neither path is strictly better than the other — they embody different tradeoffs. But having both at the same file-shape, writing the same cache, with no provenance marker, is the single most load-bearing issue in this directory.

### 1.3 Where the skills side comes from

Stage 2 ("skill enrichment") is in practice done inside stage 1, not as a separate pass. Both `scrape_pdf.py` and `extract.py` ask Gemini to emit `skill_mappings` alongside course fields in the same call. `pipeline/run.py` has a fallback to `ontology.skills.derive_skills` for the case where the enriched cache is missing and `skip_skills` is false, but for the PDF pipeline that fallback is unreachable in practice.

## 2. Evaluation

### 2.1 Quality

**Page filtering robustness.** Both pipelines filter pages using the same general heuristic — count course-code regex matches per page and require ≥2. The two regexes diverge in an important way: `scrape_pdf.py`'s `[A-Z]{2,6}\s+\d{1,4}[A-Z]?` requires 2–6 uppercase letters *with no spaces between them*, so it **fails to match multi-word department codes like "C S 1A" (Computer Science at Foothill) or "MED A 10"**, and it misses numeric suffixes like "101L" (only `[A-Z]?` after the digits, not `[A-Z]{0,2}`). `extract.py`'s regex catches these. Pages containing only multi-word-code courses will silently fall below the 2-hit threshold and be dropped. The fallback "if <10% of pages match, process all pages" masks this for image-based PDFs but not for the text-extractable catalogs where the regex is running successfully but partially.

**Coverage as empirically observed.** The coverage files from `extract.py` show patterns worth noting:
- Foothill: 1766 courses extracted, MCF-matched 426, **avg 4.8 skills/course** — below the "at least 6" target the prompt asks for.
- Alameda: 597 courses, MCF-matched 262, avg 4.5 skills/course, 2 chunks failed.
The skill-count under-delivery is consistent. The model is not honoring the "≥6" instruction in practice, and nothing in the pipeline enforces it.

**MCF match rate is low.** 426 / 1766 for Foothill ≈ 24%. This is partly because MCF only covers CTE/credit courses and catalogs contain non-credit and general-ed courses, but it also reflects brittle code normalization: MCF codes are 12-char fixed-width ("CS      1A  "), catalog codes come in whatever form the model emits ("C S 1A", "CS 1A", "CS-1A"), and `_normalize_course_id` handles only one of those variants. `_cross_reference_mcf` does `re.sub(r"\s+", " ", code).strip()` as a second attempt, but doesn't try stripping spaces entirely, uppercasing, or normalizing hyphens.

**Program-table contamination.** The `scrape_pdf.py` system prompt explicitly tells the model to skip program requirement tables, but there is no programmatic check. Dedupe is by exact `code` match, so a program table entry like "CS 1A" that happens to repeat the real course code will be merged (the more complete entry wins). But a program entry with a slightly different code format — "CS1A" vs "CS 1A" — becomes a ghost duplicate that both survives dedupe *and* fails MCF lookup.

**Description cleanup.** `_to_raw_course` in `scrape_pdf.py` strips a trailing `YYYY.MM` pattern from descriptions — this is specifically to handle a catalog-effective-date artifact, but there's no test pinning that behavior, and no other sanitization (footer text, page numbers, trailing whitespace runs).

**Extraction fidelity.** There is no ground-truth comparison anywhere in the codebase. The `courses.md` product doc appeals to "a knowledgeable reviewer" passing the inspection. The `_coverage.json` metrics are volume and taxonomy-conformance metrics, not fidelity metrics. There's no spot-check fixture, no gold-standard comparison set, no diff-against-previous-run.

**Scraper paths never run.** `scrape.py` (CourseLeaf) and `scrape_curricunet.py` are full-featured HTML scrapers (382 and 521 lines respectively) that produce higher-fidelity source data than scraping PDFs ever will — they pull the actual COR with per-field labels — but they are not wired into the pipeline. If the goal is fidelity, the scraper paths are the right input surface for ~90%+ of California community colleges (CourseLeaf + CurricUNET together cover most of the state).

**Skill taxonomy drift.** `extract.py` uses `pipeline/extraction_prompt.txt`, which hardcodes the skill vocabulary as static text. `scrape_pdf.py` interpolates `TAXONOMY_LIST` at call time from `ontology.skills.UNIFIED_TAXONOMY`. Any change to `ontology/skills.py` will make the two paths drift apart in what skills they consider valid. Since the `load.py` loader also validates against `UNIFIED_TAXONOMY` at write time, `extract.py`'s output will see skills silently dropped in the loader if the frozen prompt has skills that no longer exist in the taxonomy.

**CurricUNET enumeration brittleness.** `_find_max_entity_id` has a subtle logic issue: on "found_above", it updates `ceiling` and breaks the inner loop, then the outer `while` unconditionally runs `ceiling *= 2`. The ceiling keeps doubling regardless of whether the probe was productive — the function overshoots the real max but then binary-searches back down, so correctness is preserved, just at ~2× wasted probes. The HEAD-based `_probe_entity` check uses `content_length > 500` as the "valid course" signal, which is undocumented and fragile to template changes.

### 2.2 Efficiency

**Token cost per college.** `scrape_pdf.py` uploads each page-range chunk as a **PDF file** to Gemini. Gemini bills document-input tokens differently from text tokens, and includes layout/OCR in the work it does — substantially more expensive per page than sending pre-extracted text. For the vast majority of California community college catalogs (which are text-extractable PDFs generated from Word/InDesign), `pypdf` extraction followed by a text-only prompt would achieve the same extraction quality at roughly 5–10× lower token cost. `extract.py` already does this — the active pipeline is using the wrong side of that tradeoff.

**Page-batch tuning.** `PAGES_PER_BATCH = 25` (scrape_pdf) vs `PAGES_PER_CHUNK = 10` (extract). The scrape_pdf value was chosen to trade off 429 rate-limit headroom against output truncation risk. `max_output_tokens=65536` is high enough that 25 pages of course descriptions rarely truncate, but when they do the halving retry is an extra full round-trip per failure. extract.py's 10-page chunks are safer but run 2.5× more calls per college.

**Cache hit rate.** PDF download is cached. Page filtering re-runs every time. Extraction re-runs every time unless `run.py` sees the enriched cache exists. There's no fine-grained cache at the chunk level — one bad chunk means either losing those courses silently or re-extracting the entire college.

**Concurrency.** `CONCURRENCY=5` for scrape_pdf is conservative — the rate-limit behavior of Gemini Flash allows higher. `extract.py` runs 10. CurricUNET enumeration uses `SCAN_CONCURRENCY=30` which is fine for enumeration (HEAD requests) but `CONCURRENCY=10` for page fetch, which should be tolerable for most CurricUNET instances.

**Rate-limit abort.** `scrape_pdf.py` has a nice `RATE_LIMIT_ABORT_THRESHOLD = 5` circuit breaker that short-circuits all in-flight tasks once Gemini has returned 5 consecutive 429s. `extract.py` has no equivalent — it will retry with exponential backoff indefinitely up to 5 attempts per task, burning wall-clock time.

**Parser speed.** The stdlib HTMLParser-based scrapers are fast enough for the catalog sizes involved (~1000 course pages per college). No concern.

**Retry on scraper failures.** `_fetch` in `scrape.py` retries RequestError 3 times with a fixed 1-second sleep, but returns `None` immediately on any non-200/non-404 status. Transient 5xx responses get no retry. CurricUNET is worse: 500 is treated as "not found" because that's how CurricUNET signals invalid IDs, but a real server-side 500 during enumeration would be indistinguishable from a missing ID.

## 3. Concrete improvements (ordered by impact)

### 3.1 Pick one extraction pipeline and delete the other

The two-implementation state is the single biggest cost. My recommendation: **keep the `extract.py` shape (pypdf text pre-extraction, MCF cross-reference, coverage report, taxonomy validation), discard the `scrape_pdf.py` shape (upload PDF to Gemini), and retire the file.** Rationale:

- Text-only prompts cost substantially less.
- Coverage reporting exists and is useful.
- MCF cross-reference is genuinely needed downstream (student generation uses TOP codes).
- The skill validation loop already handles off-taxonomy drop-with-log.

But `extract.py` also has problems that must be fixed before it can be the canonical path: dependency direction, hardcoded path, and static taxonomy prompt. Those are covered in §3.3 and §4.

Alternative: keep `scrape_pdf.py` because it's the one wired in and handles image-based catalogs via PDF upload. In that case the delta work is: add MCF cross-reference, add coverage reporting, add provenance field.

Either direction is defensible. The *status quo of keeping both* is not.

**Expected impact:** One authoritative extraction path, ~2–5× lower per-college Gemini cost if the text path wins, unambiguous cache provenance.

### 3.2 Wire in `scrape.py` and `scrape_curricunet.py` for the colleges they can serve

The HTML scrapers produce higher-fidelity source data than PDF extraction can, because they read the actual COR field-by-field. They exist, they work (based on code review — no runtime check was performed), and they are orphaned. Wiring them in requires:

1. Extending `pipeline/catalog_sources.json` (or the equivalent COLLEGES manifest in `run.py`) with a `scraper_type` discriminator: `courseleaf` | `curricunet` | `pdf`.
2. A small dispatch in `run.py`'s stage 1 to pick the scraper.
3. For scrapers that don't produce `skill_mappings`, letting the existing `derive_skills` fallback in `run.py` do a separate stage 2 pass.

I am **not** proposing to do the wiring in this session — it touches `pipeline/run.py`, which is out of scope for this pass. See §4.

**Expected impact:** For CourseLeaf/CurricUNET colleges, extraction fidelity goes from "LLM interpretation of a page of prose" to "direct read of the institution's structured COR fields." This is the highest-leverage fidelity improvement available.

### 3.3 Fix `extract.py`'s dependency and path bugs

Three issues, all fixable inside `backend/courses/`:

- **Import direction:** `from pipeline.mcf_key_map import pdf_to_mcf_key` violates the documented feature → pipeline direction. The `pdf_to_mcf_key` helper should be moved to `ontology/` (probably `ontology/mcf_lookup.py`, which is already the MCF authority). This requires touching shared infrastructure — see §4.
- **Hardcoded path:** `MCF_DIR = Path("/Users/dayonekoo/Desktop/cc_dataset/mastercoursefiles")` should point at the in-repo `ontology/mastercoursefiles/` directory the README designates. Fixable inside `backend/courses/`.
- **Static taxonomy prompt:** `extraction_prompt.txt` hardcodes the skill vocabulary. Switch to runtime interpolation the way `scrape_pdf.py` does. Fixable inside `backend/courses/` — the prompt file lives under `pipeline/` but can be rewritten with a `{taxonomy}` placeholder; the loader is in `extract.py`.

**Expected impact:** Removes silent drift between `ontology/skills.py` and the extraction prompt. Makes `extract.py` runnable on any machine. Removes the one documented layering violation in the courses directory.

### 3.4 Unify and tighten the course-code regex

Adopt the stricter pattern from `extract.py` (`\b[A-Z][A-Z .]{1,8}\s*\d{1,4}[A-Z]{0,2}\b`) as the single regex used by whichever extraction path survives §3.1. Test it against fixtures drawn from a handful of real catalogs — Foothill (multi-word codes like "C S 1A"), CCSF (numeric suffixes like "CS 110A"), Allan Hancock (three-letter prefixes with letter suffixes).

**Expected impact:** Catches courses the current scrape_pdf regex silently drops.

### 3.5 Add a provenance field to the enriched cache

Stamp each `{college}_enriched.json` with:

```json
{
  "_meta": {
    "extractor": "scrape_pdf" | "extract" | "courseleaf" | "curricunet",
    "extractor_version": "...",
    "extracted_at": "2026-04-11T...",
    "pdf_url": "...",
    "taxonomy_hash": "..."
  },
  "courses": [ ... ]
}
```

Requires a shape change the loader has to accept. The `taxonomy_hash` is a hash of the sorted `UNIFIED_TAXONOMY` at extraction time — cheap invalidation signal when the taxonomy evolves.

**Expected impact:** Provenance debugging. Cache-invalidation when taxonomy changes. Answers the question "which extractor produced this file?" deterministically.

### 3.6 Normalize course codes before dedupe and MCF lookup

Add a single canonical form — uppercase, collapse whitespace, remove hyphens — applied at three points: dedupe key, MCF lookup key, and before Neo4j MERGE. Keep the original code in a `code_raw` field for display. The existing `_normalize_course_id` in `extract.py` is a partial attempt but only handles one edge case.

**Expected impact:** Higher MCF match rate (currently ~24% for Foothill). Fewer ghost duplicates.

### 3.7 Add unit tests for the pure-function surface

Pure-logic targets in `backend/courses/` that should be tested, ordered by leverage:

| File | Function | What to test |
|---|---|---|
| `extract.py` | `_normalize_course_id` | Round-trips MCF 12-char form to catalog form for multi-word, fixed-width, and hyphenated inputs |
| `extract.py` | `_is_course_page` | Flags pages with ≥2 codes + ≥2 keywords; rejects short pages, program-table pages |
| `extract.py` | `_chunk_pages` | Respects `PAGES_PER_CHUNK` and `MAX_CHARS_PER_CHUNK`; never drops pages |
| `scrape_pdf.py` / `extract.py` | `_deduplicate_courses` | Collapses by code, keeps most-populated entry, survives empty codes |
| `extract.py` | `_validate_skills` | Drops off-taxonomy terms, preserves order, dedupes within course |
| `extract.py` | `_cross_reference_mcf` | Matches on exact code and whitespace-collapsed code; backfills only missing units |
| `scrape_pdf.py` | `_filter_course_pages` heuristic | Split the pypdf I/O from the decision function; test the decision function on synthetic page text |
| `scrape_pdf.py` | `_to_raw_course`, `_ensure_str_list` | Field coercion; year-stamp stripping |
| `scrape.py` | `CourseOutlineParser._parse_h1`, `_assign_cor_field` | Title parsing and label-to-field mapping across Foothill and Citrus shapes |
| `scrape_curricunet.py` | `CurricUNETCourseParser._parse_title` | "CDEV 67 - Child, Family, and Community" → (code, name, dept) |

All of these are stdlib + pure Python — no Neo4j, no Gemini, no network. A single session could land all of them. Each file needs the required module docstring with a `Coverage:` section per `backend/docs/testing.md`.

**Expected impact:** First real quality gate in the courses directory. Prevents regressions to the normalization/dedupe/validation logic — exactly the places where bugs have silently eaten courses in the past.

### 3.8 Add a coverage report to the active pipeline

Whichever extraction path survives §3.1 should write `{college}_coverage.json` — the `extract.py` shape is a good starting point. Include at least:

- `pdf_pages_total`, `pdf_pages_with_courses`, `chunks_failed`
- `courses_extracted`, `courses_with_skills`, `avg_skills_per_course`
- `mcf_matched`, `mcf_unmatched_sample` (first 20 unmatched codes — useful for normalization debugging)
- `taxonomy_skills`, `off_taxonomy_skills`
- `extraction_seconds`, `gemini_calls`, `gemini_retries`

**Expected impact:** Answers "did this college extract well?" without re-reading 1800 courses by hand.

### 3.9 Enforce the skill-count floor

The "≥6 skills per course" instruction is silently under-delivered (4.8 avg Foothill, 4.5 Alameda). Either:

- Drop the floor to a realistic value (4) and update the prompt, or
- Retry courses that come back with <6 skills in a follow-up Gemini call with only that course's content (much cheaper than a full chunk retry).

Given the product doc's emphasis on skill fidelity, I'd recommend option 2 for courses with <4 skills (clear under-extraction) and accepting 4–5 as a real distribution.

**Expected impact:** Closes the gap between stated and actual skill-count policy.

## 4. Coordination requests (touch shared infrastructure)

These items cannot be landed without changes outside `backend/courses/`, so per the session constraints they are surfaced rather than implemented.

1. **Move `pipeline/mcf_key_map.py` functions into `ontology/mcf_lookup.py`.** Motivation: `courses/extract.py` currently imports from `pipeline/`, which `backend/README.md` explicitly forbids ("features never import from pipeline/"). `mcf_key_map` is ontology-adjacent — it translates between a college key and an MCF filename key. `ontology/mcf_lookup.py` is the documented home for MCF-side helpers. This also lets any other feature (e.g. `occupations/`, `students/`) use the same key mapping without a layering violation.

2. **Move the canonical MCF data location or document the current one.** `extract.py` hardcodes `/Users/dayonekoo/Desktop/cc_dataset/mastercoursefiles`. `backend/README.md` points at `ontology/mastercoursefiles/`. These need to be the same directory, and `extract.py` needs to read from it via a relative path.

3. **Wire the HTML scrapers into `pipeline/run.py`.** `scrape.py` (CourseLeaf) and `scrape_curricunet.py` (CurricUNET) are implemented but never called. Wiring requires editing `pipeline/run.py` to dispatch on a `scraper_type` field in `catalog_sources.json`, plus extending the manifest. This is a substantial structural change to `pipeline/run.py` and should be scoped as its own session.

4. **Taxonomy-change cache invalidation.** If §3.5 (provenance + taxonomy hash) is adopted, `pipeline/run.py`'s cache-skip logic should be extended to invalidate enriched caches when `UNIFIED_TAXONOMY` has changed since extraction. This is a small `run.py` change but is outside `backend/courses/`.

5. **Pipeline orchestration tests.** `backend/docs/testing.md` lists `pipeline/run.py` as explicitly out of scope for unit tests. The integration smoke of "does extract → load still produce a non-empty graph?" is not tested anywhere. This is a cross-cutting testing-scope question, not a courses-local question, and belongs in a dedicated proposal if pursued.

## 5. Suggested next-session scope

If the above is approved, a reasonable first implementation session is:

- **§3.1** (pick one path and retire the other),
- **§3.3** (in the courses-local subset: fix hardcoded path, fix taxonomy drift; defer the `mcf_key_map` move until coordination request #1 is resolved),
- **§3.4** (unified regex),
- **§3.7** (unit tests for the surviving extraction path's pure functions).

Everything else depends on either the coordination requests landing first or on decisions that should be made at the pipeline-wide level rather than inside `backend/courses/`.
