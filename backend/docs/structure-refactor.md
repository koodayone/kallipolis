# Backend structure refactor plan

## Goal

Restructure `backend/` from a layer-primary layout (`api/`, `workflows/`, `pipeline/`, `models/`) into a feature-primary layout where each ontology unit owns a directory containing everything about that unit. Cross-cutting infrastructure (Neo4j graph, LLM, shared taxonomy) lives in small shared dirs.

The point: collapse the doc-to-code mapping to one hop. `docs/product/students.md` → `backend/students/`. An agent or reader who understands the ontology can find the code without a second search.

## Rationale (short)

The current tree hides scope behind generic names:

- `ontology/` is academic-only (contains only GPA / primary-focus helpers)
- `api/ontology.py` is academic-only (colleges, departments, courses, students)
- `pipeline/loader.py` is academic-only (`pipeline/industry/loader.py` is the other half)
- `workflows/` mixes retrieval (`*_query.py`), generation (`partnerships.py`, `swp.py`), and LLM infrastructure (`query_engine.py`) with no structural signal
- `models/__init__.py` is a 280-line monolith mixing all six units
- `workflows/swp.py` reaches into `pipeline/industry/{coe_supply,mcf_lookup,region_maps}` for runtime helpers — these aren't pipeline code, they're shared reference data living in the wrong place

Feature folders fix all of this at once. Layer-primary alternatives were considered and rejected — see the design discussion in conversation history. The decisive factor: Kallipolis docs are unit-primary, the audit is unit-primary, and `MEMORY.md` notes semantic legibility as an MVP sequencing priority.

## Target layout

```
backend/
├── main.py                        # FastAPI entry; imports routers from each feature
│
├── ontology/                      # Cross-unit schema and shared reference data
│   ├── schema.py                  # Neo4j driver, constraints, init  (unchanged file)
│   ├── skills.py                  # Unified taxonomy  (was pipeline/skills.py)
│   ├── regions.py                 # College/Metro/COE region mapping  (was pipeline/industry/region_maps.py)
│   ├── crosswalks.py              # SOC/NAICS crosswalks  (was pipeline/industry/crosswalks.py)
│   ├── mcf_lookup.py              # TOP6 code resolution  (was pipeline/industry/mcf_lookup.py)
│   └── supply.py                  # Supply/demand helpers  (was pipeline/industry/coe_supply.py)
│
├── llm/                           # Shared LLM infrastructure
│   └── query_engine.py            # Cypher generation + validation  (was workflows/query_engine.py)
│
├── students/                      # ↔ docs/product/students.md
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/ontology.py)
│   ├── query.py                   # LLM retrieval  (was workflows/student_query.py)
│   ├── generate.py                # Synthetic generator  (was pipeline/students.py)
│   └── helpers.py                 # GPA, primary focus  (was ontology/utils.py)
│
├── courses/                       # ↔ docs/product/courses.md
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/ontology.py)
│   ├── query.py                   # LLM retrieval  (was workflows/course_query.py)
│   ├── scrape.py                  # Catalog scraper  (was pipeline/scraper.py, defines RawCourse)
│   ├── scrape_curricunet.py       # CurricuNet variant  (was pipeline/scraper_curricunet.py)
│   ├── scrape_pdf.py              # PDF catalog variant  (was pipeline/scraper_pdf.py)
│   ├── extract.py                 # PDF → structured  (was pipeline/extract.py)
│   └── load.py                    # Neo4j loader — also creates College, Department container nodes  (was pipeline/loader.py)
│
├── occupations/                   # ↔ docs/product/occupations.md
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/labor_market.py)
│   ├── query.py                   # LLM retrieval  (was workflows/occupation_query.py)
│   ├── generate.py                # COE → occupations.json  (was pipeline/industry/generate_occupations_from_coe.py)
│   ├── assign_skills.py           # SOC → skills mapping  (was pipeline/industry/assign_occupation_skills.py)
│   ├── descriptions.py            # Occupation descriptions  (was pipeline/industry/descriptions.py)
│   ├── coe_parser.py              # COE data authority parser  (was pipeline/industry/coe_parser.py)
│   └── load.py                    # Neo4j loader  (was pipeline/industry/loader.py — load_industry)
│
├── employers/                     # ↔ docs/product/employers.md
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/labor_market.py)
│   ├── query.py                   # LLM retrieval  (was workflows/employer_query.py)
│   ├── generate.py                # Employer generation  (was pipeline/industry/generate_employers.py)
│   ├── edd_scrape.py              # EDD data authority scraper  (was pipeline/industry/edd_employers.py)
│   └── load.py                    # Neo4j loader  (was pipeline/industry/employers.py)
│
├── partnerships/                  # ↔ docs/product/partnerships.md (unit of action)
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/workflows.py)
│   ├── query.py                   # Partnership Landscape retrieval  (was workflows/partnerships_query.py)
│   └── generate.py                # Proposal generation — the 71KB file  (was workflows/partnerships.py; internal split deferred to PR 2)
│
├── strong_workforce/              # ↔ docs/product/strong-workforce.md (unit of action)
│   ├── models.py                  # Pydantic  (extracted from models/__init__.py)
│   ├── api.py                     # Routes  (extracted from api/workflows.py)
│   └── generate.py                # SWP project generation  (was workflows/swp.py)
│
├── pipeline/                      # Orchestration + cross-cutting prep scripts
│   ├── run.py                     # Main orchestrator — imports updated  (unchanged location)
│   ├── reload.py                  # Reset + reingest — imports updated  (unchanged location)
│   ├── load_skills.py             # Load unified taxonomy into Neo4j  (unchanged location)
│   ├── build_calibrations.py      # TOP-code calibration prep  (unchanged location)
│   ├── build_prefix_mapping.py    # MCF prefix lookup prep  (unchanged location)
│   ├── mcf_key_map.py             # Pipeline-time MCF key mapping  (unchanged location)
│   ├── prepare_taxonomy_sources.py
│   ├── validate_sources.py
│   └── calibrations/
│       └── parse_top4.py
│
├── scripts/
│   └── materialize_student_fields.py
│
├── tests/
│   ├── test_advisory_board.py
│   ├── test_gap_identification.py
│   ├── test_occupation_selection.py
│   └── test_primary_department.py
│
└── docs/
    ├── coci-outreach-draft.md
    └── structure-refactor.md      # this file
```

## Complete file migration map

**Legend:** `→ MOVE` = git mv, `→ SPLIT` = file content partitioned into multiple destinations, `→ STAY` = unchanged location (imports may still need updating).

### `backend/main.py`
- → STAY. Update imports:
  - `from api.ontology import router as ontology_router` → removed; replaced by per-feature imports
  - `from api.workflows import router as workflows_router` → removed
  - `from api.labor_market import router as labor_market_router` → removed
  - Add: `from students.api import router as students_router`
  - Add: `from courses.api import router as courses_router`
  - Add: `from occupations.api import router as occupations_router`
  - Add: `from employers.api import router as employers_router`
  - Add: `from partnerships.api import router as partnerships_router`
  - Add: `from strong_workforce.api import router as strong_workforce_router`
  - `app.include_router(...)` calls updated in parallel. Route prefixes and tags preserved so the frontend doesn't break.

### `backend/ontology/`
- `schema.py` → STAY at `ontology/schema.py`.
- `utils.py` → MOVE to `students/helpers.py` (only `compute_gpa` and `compute_primary_focus` live here; only `students/*` and `scripts/materialize_student_fields.py` import it).
- `__init__.py` → STAY (empty).

### `backend/models/__init__.py`
- → SPLIT. Partition the 280 lines by unit. Every class moves to `<unit>/models.py`:
  - `StudentSummary`, `StudentQueryResponse`, and any other Student types → `students/models.py`
  - `CourseSummary`, `DepartmentSummary`, `CourseQueryResponse` → `courses/models.py`
  - `OccupationSummary`, `OccupationMatch`, `OccupationQueryResponse` → `occupations/models.py`
  - `EmployerSummary`, `EmployerMatch`, `EmployerQueryResponse` → `employers/models.py`
  - `NarrativeProposal`, `PartnershipOpportunity`, and any partnership types → `partnerships/models.py`
  - `SwpProject`, `SwpMetadata`, and any SWP types → `strong_workforce/models.py`
- Delete `backend/models/` directory entirely.
- **Verify before splitting:** Read the full file and produce a class-by-class inventory. Any type genuinely shared across units (unlikely given the earlier analysis) goes to the most-dependent unit or to `ontology/models.py` if cross-unit.

### `backend/api/`
- `__init__.py` → DELETE.
- `ontology.py` → SPLIT by route group:
  - Student routes → `students/api.py`
  - Course routes → `courses/api.py`
  - College/Department routes → placement TBD (see Open Questions — likely `courses/api.py` since Department is a course container)
  - Preserve `/ontology` URL prefix via main.py (or migrate the frontend to new prefixes in a separate PR — see Open Questions)
  - Update imports at the top (was `from ontology.schema import get_driver`, `from ontology.utils import compute_gpa`, `from workflows.student_query import run_student_query`, `from workflows.course_query import run_course_query`)
- `labor_market.py` → SPLIT:
  - Occupation routes → `occupations/api.py`
  - Employer routes → `employers/api.py`
  - Region routes (if any) → `ontology/api.py` or merged into one of the above (see Open Questions)
- `workflows.py` → SPLIT:
  - Partnership endpoints (`run_targeted_proposal`, `stream_targeted_proposal`) → `partnerships/api.py`
  - SWP endpoints (`get_lmi_context`, `stream_swp_project`) → `strong_workforce/api.py`
  - Report endpoint (`run_report`) and Ingestion endpoint (`run_ingest`) → DEFER (see Open Questions — these are placeholders per the earlier analysis)

### `backend/workflows/`
- `query_engine.py` → MOVE to `llm/query_engine.py`.
- `student_query.py` → MOVE to `students/query.py`.
- `course_query.py` → MOVE to `courses/query.py`.
- `occupation_query.py` → MOVE to `occupations/query.py`.
- `employer_query.py` → MOVE to `employers/query.py`.
- `partnerships_query.py` → MOVE to `partnerships/query.py`.
- `partnerships.py` → MOVE to `partnerships/generate.py`. **Internal split deferred to PR 2.**
- `swp.py` → MOVE to `strong_workforce/generate.py`. Update imports:
  - `from pipeline.industry.coe_supply import get_coe_supply, get_coe_demand` → `from ontology.supply import get_coe_supply, get_coe_demand`
  - `from pipeline.industry.mcf_lookup import lookup_top6` → `from ontology.mcf_lookup import lookup_top6`
  - `from pipeline.industry.region_maps import COLLEGE_COE_REGION` → `from ontology.regions import COLLEGE_COE_REGION`
- `report.py` → DEFER. Placeholder. See Open Questions.
- `ingestion.py` → DEFER. Placeholder. See Open Questions.
- `__init__.py` → DELETE.

### `backend/pipeline/` (curriculum-side and cross-cutting)
- `scraper.py` → MOVE to `courses/scrape.py`. Defines `RawCourse` which is imported by `pipeline/run.py`, `courses/scrape_pdf.py`, `courses/scrape_curricunet.py`, and `ontology/skills.py`.
- `scraper_curricunet.py` → MOVE to `courses/scrape_curricunet.py`.
- `scraper_pdf.py` → MOVE to `courses/scrape_pdf.py`.
- `extract.py` → MOVE to `courses/extract.py`. Update its internal late imports (`from pipeline.skills import UNIFIED_TAXONOMY` → `from ontology.skills import UNIFIED_TAXONOMY`, `from pipeline.mcf_key_map import ...` → unchanged).
- `skills.py` → MOVE to `ontology/skills.py`. This is the unified taxonomy — used by both curriculum-side and industry-side code. It lives in `ontology/` because it's the semantic center of the ontology, per `docs/product/the-skills-taxonomy.md`.
- `loader.py` → MOVE to `courses/load.py`. Update `from pipeline.skills import UNIFIED_TAXONOMY` → `from ontology.skills import UNIFIED_TAXONOMY`.
- `students.py` → MOVE to `students/generate.py`. Update `from ontology.utils import compute_gpa, compute_primary_focus` → `from students.helpers import compute_gpa, compute_primary_focus`.
- `run.py` → STAY. Update imports:
  - `from pipeline.scraper import RawCourse` → `from courses.scrape import RawCourse`
  - `from pipeline.skills import derive_skills` → `from ontology.skills import derive_skills`
  - `from pipeline.loader import load_college, CollegeConfig, LoadStats` → `from courses.load import load_college, CollegeConfig, LoadStats`
  - Late imports inside functions updated similarly.
- `reload.py` → STAY. Update imports:
  - `from pipeline.loader import load_college, CollegeConfig` → `from courses.load import load_college, CollegeConfig`
  - `from pipeline.students import generate_and_load_students` → `from students.generate import generate_and_load_students`
  - `from pipeline.industry.loader import load_industry` → `from occupations.load import load_industry`
  - `from pipeline.industry.employers import load_employers, cleanup_stale_employers` → `from employers.load import load_employers, cleanup_stale_employers`
- `load_skills.py` → STAY.
- `build_calibrations.py` → STAY.
- `build_prefix_mapping.py` → STAY.
- `mcf_key_map.py` → STAY. (Pipeline-time key mapping; different from `ontology/mcf_lookup.py` which is a runtime helper.)
- `prepare_taxonomy_sources.py` → STAY.
- `validate_sources.py` → STAY.
- `calibrations/parse_top4.py` → STAY.
- `__init__.py` → STAY (empty).

### `backend/pipeline/industry/` (labor market side)
- `generate_occupations_from_coe.py` → MOVE to `occupations/generate.py`.
- `generate_employers.py` → MOVE to `employers/generate.py`. Update imports:
  - `from pipeline.industry.region_maps import ...` → `from ontology.regions import ...`
  - `from pipeline.industry.edd_employers import ...` → `from employers.edd_scrape import ...`
- `assign_occupation_skills.py` → MOVE to `occupations/assign_skills.py`. Update `from pipeline.skills import UNIFIED_TAXONOMY` → `from ontology.skills import UNIFIED_TAXONOMY`.
- `coe_parser.py` → MOVE to `occupations/coe_parser.py`.
- `coe_supply.py` → MOVE to `ontology/supply.py`. This is a runtime helper (used by `strong_workforce/generate.py`), not ingestion. It maps TOP codes to student completions — cross-unit conceptually. Update `from pipeline.industry.region_maps import COLLEGE_COE_REGION` → `from ontology.regions import COLLEGE_COE_REGION`.
- `edd_employers.py` → MOVE to `employers/edd_scrape.py`.
- `oews_parser.py` → DEFER. "Mostly deprecated" per earlier analysis. See Open Questions.
- `descriptions.py` → MOVE to `occupations/descriptions.py`.
- `crosswalks.py` → MOVE to `ontology/crosswalks.py`. SOC/NAICS crosswalks are cross-unit reference data.
- `mcf_lookup.py` → MOVE to `ontology/mcf_lookup.py`. Runtime helper; used by `strong_workforce/generate.py`. Update `from pipeline.industry.coe_supply import _normalize_college` → `from ontology.supply import _normalize_college`.
- `region_maps.py` → MOVE to `ontology/regions.py`. Region is a first-class graph concept (`College-[:IN_MARKET]->Region`, `Employer-[:IN_MARKET]->Region`), not an industry-specific constant.
- `employers.py` → MOVE to `employers/load.py`.
- `loader.py` → MOVE to `occupations/load.py`. Defines `load_industry`. Update `from pipeline.industry.region_maps import ...` → `from ontology.regions import ...`.
- `__init__.py` → DELETE.

### `backend/tests/`
- All files → STAY. Update imports:
  - `test_gap_identification.py`: `from workflows.partnerships import (...)` → `from partnerships.generate import (...)`
  - `test_primary_department.py`: same
  - `test_occupation_selection.py`: `from workflows.partnerships import (...)` → `from partnerships.generate import (...)`; `from ontology.schema import get_driver` → STAY
  - `test_advisory_board.py`: `from workflows.partnerships import (...)` → `from partnerships.generate import (...)`

### `backend/scripts/`
- `materialize_student_fields.py` → STAY. Update imports:
  - `from ontology.utils import compute_gpa, compute_primary_focus` → `from students.helpers import compute_gpa, compute_primary_focus`
  - `from ontology.schema import get_driver` → STAY

### Generated artifacts (not moved)
- `pipeline/cache/`, `pipeline/industry/cache/`, `pipeline/industry/mastercoursefiles/`, `pipeline/industry/occupations_pre_expansion.json` — all stay. Pipeline code still writes/reads from these paths unchanged.

## Cross-cutting import surface

Every import referencing the old module paths must update. Complete list from `rg` output, grouped by source module:

**From `ontology.schema`** (Neo4j driver/constraints) → unchanged.
**From `ontology.utils`** → `from students.helpers` (only compute_gpa, compute_primary_focus).
**From `pipeline.skills`** → `from ontology.skills`.
**From `pipeline.scraper`** → `from courses.scrape`.
**From `pipeline.scraper_pdf`** → `from courses.scrape_pdf`.
**From `pipeline.scraper_curricunet`** → `from courses.scrape_curricunet`.
**From `pipeline.extract`** → `from courses.extract`.
**From `pipeline.loader`** → `from courses.load`.
**From `pipeline.students`** → `from students.generate`.
**From `pipeline.mcf_key_map`** → unchanged (still in pipeline/).
**From `pipeline.industry.region_maps`** → `from ontology.regions`.
**From `pipeline.industry.coe_supply`** → `from ontology.supply`.
**From `pipeline.industry.mcf_lookup`** → `from ontology.mcf_lookup`.
**From `pipeline.industry.crosswalks`** → `from ontology.crosswalks`.
**From `pipeline.industry.edd_employers`** → `from employers.edd_scrape`.
**From `pipeline.industry.employers`** → `from employers.load`.
**From `pipeline.industry.loader`** → `from occupations.load`.
**From `pipeline.industry.generate_employers`** → `from employers.generate`.
**From `pipeline.industry.generate_occupations_from_coe`** → `from occupations.generate`.
**From `pipeline.industry.assign_occupation_skills`** → `from occupations.assign_skills`.
**From `pipeline.industry.descriptions`** → `from occupations.descriptions`.
**From `pipeline.industry.coe_parser`** → `from occupations.coe_parser`.
**From `workflows.query_engine`** → `from llm.query_engine`.
**From `workflows.student_query`** → `from students.query`.
**From `workflows.course_query`** → `from courses.query`.
**From `workflows.occupation_query`** → `from occupations.query`.
**From `workflows.employer_query`** → `from employers.query`.
**From `workflows.partnerships_query`** → `from partnerships.query`.
**From `workflows.partnerships`** → `from partnerships.generate`.
**From `workflows.swp`** → `from strong_workforce.generate`.
**From `models`** → `from <unit>.models` (depends on which class is imported).
**From `api.ontology`** → deleted; main.py now imports per-feature routers.
**From `api.labor_market`** → deleted; same.
**From `api.workflows`** → deleted; same.

Also: `workflows/swp.py` currently does late imports inside functions for `pipeline.industry.region_maps`. Those need updating too (grep will catch them).

## Execution as two PRs

### PR 1 — Mechanical refactor (single atomic commit)

All of the following in one commit. The diff will be large but every hunk is mechanical — either a `git mv`, an import-path update, or a partition of `models/__init__.py` by class.

1. Create new directories: `backend/llm/`, `backend/students/`, `backend/courses/`, `backend/occupations/`, `backend/employers/`, `backend/partnerships/`, `backend/strong_workforce/`. Add empty `__init__.py` to each.
2. Execute all file moves via `git mv` where possible (preserves history). For `SPLIT` files (`models/__init__.py`, `api/ontology.py`, `api/labor_market.py`, `api/workflows.py`), create the new per-feature files and delete the originals in the same commit.
3. Update every import across the codebase (grep will find them; the list above is the authoritative map).
4. Delete empty `__init__.py` files and empty directories: `backend/models/`, `backend/api/`, `backend/workflows/`, `backend/pipeline/industry/`.
5. Run the verification steps below.

**Not in PR 1:**
- No internal split of `partnerships/generate.py` (71KB monolith). It moves as-is.
- No deletion of placeholder `workflows/report.py` or `workflows/ingestion.py` — deferred pending confirmation they are unused (see Open Questions).
- No URL prefix changes (frontend keeps hitting `/ontology`, `/workflows`, `/labor-market` via the unchanged `main.py` router prefixes).

### PR 2 — Partnerships internal split

`partnerships/generate.py` is a 71KB file conflating gathering, filtering, and narrative generation. This is real code work requiring understanding, not a mechanical move — so it earns its own PR where the diff is readable. Proposed internal structure:

```
partnerships/
├── generate.py                    # top-level orchestrator (entry points only)
├── gather.py                      # context gathering from the graph
├── filter.py                      # department / occupation / curriculum filtering
└── narrative.py                   # LLM narrative composition
```

This split is deferred because it requires reading the full 71KB to identify seams. Doing it in PR 1 would bloat the diff with judgment calls mixed in with mechanical moves, making the whole thing unreviewable.

## Verification

After PR 1, in order:

1. **Imports resolve.** `python -c "import main"` from `backend/`. If any import fails, grep for the missing module.
2. **Tests pass.** `cd backend && python -m pytest tests/`. All four tests must pass.
3. **Pipeline runs.** `python -m pipeline.run --college foothill --from-cache` (fastest end-to-end check; no network). Should complete without import errors.
4. **Server starts.** `uvicorn main:app` from `backend/`. `/health` returns 200. One representative endpoint per feature:
   - `/ontology/college` (students/courses routes)
   - `/labor-market/occupations` (occupations/employers routes)
   - `/workflows/targeted-proposal` (partnerships/SWP routes)
5. **Frontend still works.** Atlas frontend hits the same URL prefixes (`/ontology`, `/workflows`, `/labor-market`) — no frontend changes required in PR 1.
6. **Docs audit passes.** `python3 tools/docs-audit/audit.py`. The audit verifies code-grounded claims in docs against the code. Any doc that cites an old path (e.g. `backend/pipeline/students.py`) must be updated. This is expected and part of PR 1.

## Rollback

PR 1 is one commit. `git revert` restores the previous layout atomically. Generated artifacts (`pipeline/cache/`, etc.) are untouched by the refactor, so no data is lost on rollback.

## Resolved decisions (2026-04-11)

1. **URL prefixes — UPDATE to per-feature.** PR 1 updates `main.py` to mount per-feature routers at `/students`, `/courses`, `/occupations`, `/employers`, `/partnerships`, `/strong-workforce`. The frontend (`atlas/lib/api.ts`, 21 call sites) is updated in parallel as part of PR 1. URL path mapping:

   | Old URL | New URL |
   |---|---|
   | `GET /ontology/college` | `GET /courses/college` |
   | `GET /ontology/departments` | `GET /courses/departments-full` (unused by frontend; renamed to avoid collision) |
   | `GET /ontology/students` | `GET /students/` |
   | `GET /ontology/students/{uuid}` | `GET /students/{uuid}` |
   | `POST /ontology/students/query` | `POST /students/query` |
   | `GET /ontology/courses/departments` | `GET /courses/departments` |
   | `GET /ontology/courses/list` | `GET /courses/` |
   | `POST /ontology/courses/query` | `POST /courses/query` |
   | `GET /labor-market/overview` | `GET /occupations/overview` |
   | `GET /labor-market/occupation/{soc_code}` | `GET /occupations/{soc_code}` |
   | `GET /labor-market/employers` | `GET /employers/` |
   | `GET /labor-market/employer/{name}` | `GET /employers/{name}` |
   | `POST /labor-market/employers/query` | `POST /employers/query` |
   | `POST /labor-market/occupations/query` | `POST /occupations/query` |
   | `GET /labor-market/partnership-landscape` | `GET /partnerships/landscape` |
   | `GET /labor-market/partnership-landscape/pipeline` | `GET /partnerships/employer-pipeline` |
   | `GET /labor-market/partnership-landscape/occupations` | `GET /partnerships/employer-occupations` |
   | `POST /labor-market/partnerships/query` | `POST /partnerships/query` |
   | `POST /workflows/partnerships/targeted` | `POST /partnerships/targeted` |
   | `POST /workflows/partnerships/targeted/stream` | `POST /partnerships/targeted/stream` |
   | `POST /workflows/swp/lmi-context` | `POST /strong-workforce/lmi-context` |
   | `POST /workflows/swp/project/stream` | `POST /strong-workforce/project/stream` |

2. **Placeholder workflows files — DELETE.** `workflows/report.py`, `workflows/ingestion.py`, their routes (`POST /workflows/report`, `POST /workflows/ingest`), and their models (`ReportRequest`, `IngestRequest`) are deleted entirely in PR 1. Verified unused: no frontend callers, no test callers, no internal callers outside `api/workflows.py`. The SWP workflow has replaced the report stub; no successor for the ingest stub.

3. **College and Department routes — `courses/api.py`.** As in the default: College and Department routes go in `courses/api.py` since Department is conceptually a course container.

### Secondary decisions (applying defaults)

- **`oews_parser.py`** → move to `occupations/oews_parser.py`, no content change.
- **`load_skills.py`** → stay in `pipeline/`.
- **`ontology/models.py`** → don't create; no cross-unit models exist yet.
- **`courses/` scraper files** → flat, no `courses/scrape/` subdir.

### Unused but preserved routes

- `GET /ontology/departments` — not called by the frontend. Renamed to `GET /courses/departments-full` to avoid collision with the used `GET /courses/departments`. Flagged for possible deletion in a future cleanup.
