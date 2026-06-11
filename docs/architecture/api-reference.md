# API Reference

The Kallipolis backend exposes one router per ontology unit, plus a single `/health` endpoint at the root. This document enumerates every endpoint, grouped by feature. Request and response shapes reference Pydantic models defined in each feature's `models.py` — for field-level detail, read the model definitions; they are the source of truth and this document cites them by name.

All endpoints require a `college` query parameter (for GET routes) or a `college` field in the request body (for POST routes). College scoping is the only access boundary the backend enforces — authentication happens in the atlas, not here. See [System Overview](./system-overview.md#authentication-and-scoping) for the trust model.

A liveness probe at `/health` is defined directly in `backend/main.py` and returns `{"status": "ok"}`. It is not mounted on any feature router and is not part of the feature API surface.

## Students

Defined in `backend/students/api.py`, mounted at `/students`.

The ontology no longer carries individual Student nodes (removed in the non-PII migration); the `students` unit is retained as a navigational surface. The list endpoint returns an empty page so the atlas Students view renders its placeholder.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /students` | Empty-page placeholder — no per-student data in the non-PII ontology. Query params: `college` (required), `limit` (default 100, max 5000), `offset` (default 0) | `StudentSummaryPage` |

## Courses

Defined in `backend/courses/api.py`, mounted at `/courses`. Includes College and Department container nodes, which are conceptually course groupings rather than first-class ontology units.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /courses/college` | College summary with its departments and the courses each department contains | `CollegeSummary` |
| `GET /courses/departments-full` | Alternate college-departments view with course titles grouped by department (legacy; prefer `/courses/college`) | `list[dict]` |
| `GET /courses/departments` | Department summary with course counts | `list[DepartmentSummary]` |
| `GET /courses` | Course listing for one department, with learning outcomes and skill mappings | `list[CourseSummary]` |
| `POST /courses/query` | Natural-language query translated to Cypher with safety gate | `CourseQueryResponse` |

**Required query parameters:** `/courses` takes `department` and `college`; the other GETs take only `college`. `POST /courses/query` takes a `CourseQueryRequest` body.

## Occupations

Defined in `backend/occupations/api.py`, mounted at `/occupations`. These endpoints expose the labor market demand side of the graph.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /occupations/overview` | All regions and their occupations, ranked by skill alignment with the college's curriculum | `LaborMarketOverview` |
| `GET /occupations/{soc_code}` | Full detail for one occupation, including per-skill course alignment and regional wage/employment data | `OccupationDetail` |
| `POST /occupations/query` | Natural-language query translated to Cypher with safety gate | `OccupationQueryResponse` |

## Employers

Defined in `backend/employers/api.py`, mounted at `/employers`. These endpoints expose the labor market supply side — the real organizations employers hire for the occupations regions demand.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /employers` | All employers in the college's region, ranked by skill alignment | `list[EmployerMatch]` |
| `GET /employers/{name}` | Full detail for one employer, including per-occupation skill alignment with courses | `EmployerDetail` |
| `POST /employers/query` | Natural-language query translated to Cypher with safety gate | `EmployerQueryResponse` |

## Partnerships

Defined in `backend/partnerships/api.py`, mounted at `/partnerships`. The Partnerships surface is occupation-centric: a sector accordion lists every PCAH-classified Strong Workforce sector with the CTE-reachable, regionally-demanded occupations within it; clicking one generates a deterministic per-(college, SOC) opportunity report.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /partnerships/sectors` | Sector accordion: every Strong Workforce sector with its CTE-reachable, regionally-demanded occupations | `SectorIndex` |
| `GET /partnerships/opportunity/{soc_code}` | Per-(college, SOC) partnership opportunity report — five narrative sections plus evidence blocks plus the candidate employer set | `OpportunityReport` |

Both endpoints take `college` as a query parameter. Both are deterministic and idempotent — same inputs always yield byte-identical responses, so they are safe to cache and to deep-link.

The opportunity report carries a `swp_evidence` block — the regional supply (projected program completions per TOP6) and demand (regional annual openings) totals plus the gap, scoped to the selected SOC. It is assembled deterministically by `_build_swp_evidence` in `backend/partnerships/opportunity.py` so any subsequent SWP funding justification has the empirical foundation it needs.

The report's `partnership_opportunities` block lists the regional employers hiring for the SOC, sorted by NAICS-4 industry-share (BLS OEWS PCT_TOTAL — the institutional measure of how prominent the role is within each employer's industry). This is the candidate target set the report directs the workforce development officer toward.

## How to regenerate this reference

FastAPI publishes the live OpenAPI schema at the /openapi.json URL and an interactive Swagger UI at /docs when the backend is running. This document is a static mirror of those routes, maintained in sync via the documentation audit (`tools/docs-audit/checks/api_endpoints.py`), which verifies every endpoint cited above against the actual router decorators in each feature's `api.py`. If this page drifts, the CI audit check fails.
