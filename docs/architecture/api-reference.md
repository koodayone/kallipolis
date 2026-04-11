# API Reference

The Kallipolis backend exposes one router per ontology unit, plus a single `/health` endpoint at the root. This document enumerates every endpoint, grouped by feature. Request and response shapes reference Pydantic models defined in each feature's `models.py` — for field-level detail, read the model definitions; they are the source of truth and this document cites them by name.

All endpoints require a `college` query parameter (for GET routes) or a `college` field in the request body (for POST routes). College scoping is the only access boundary the backend enforces — authentication happens in the atlas, not here. See [System Overview](./system-overview.md#authentication-and-scoping) for the trust model.

Two endpoints stream their output via server-sent events: `POST /partnerships/targeted/stream` and `POST /strong-workforce/project/stream`. Both use FastAPI's `StreamingResponse` with `text/event-stream`.

A liveness probe at `/health` is defined directly in `backend/main.py` and returns `{"status": "ok"}`. It is not mounted on any feature router and is not part of the feature API surface.

## Students

Defined in `backend/students/api.py`, mounted at `/students`.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /students` | List all students enrolled at the college, ordered by courses completed | `list[StudentSummary]` |
| `GET /students/{student_uuid}` | Full enrollment history and derived skill set for one student | `StudentDetail` |
| `POST /students/query` | Natural-language query translated to Cypher with safety gate | `StudentQueryResponse` |

**Request model** for `POST /students/query`: `StudentQueryRequest` — fields `query` (the NL question) and `college`.

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

Defined in `backend/partnerships/api.py`, mounted at `/partnerships`. This router mixes retrieval (the landscape view, which reads precomputed alignment data) with AI-backed generation (targeted proposals).

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `GET /partnerships/landscape` | Employers ranked by partnership opportunity, reading the precomputed `PARTNERSHIP_ALIGNMENT` edge | `PartnershipLandscape` |
| `GET /partnerships/employer-pipeline` | Student pipeline size (count of students with ≥3 matching skills) for one employer | `{"pipeline_size": int}` |
| `GET /partnerships/employer-occupations` | Lightweight list of occupations an employer hires for, with annual wage | `{"occupations": [...]}` |
| `POST /partnerships/query` | Natural-language query translated to Cypher with safety gate | `PartnershipQueryResponse` |
| `POST /partnerships/targeted` | Generate a targeted partnership proposal for a specific employer (non-streaming) | `NarrativeProposal` |
| `POST /partnerships/targeted/stream` | Generate a targeted partnership proposal with SSE streaming | text/event-stream |

**Request body** for `POST /partnerships/targeted` and `/partnerships/targeted/stream`: `ProposalRequest` — fields `employer`, `college`, `engagement_type` (one of `internship`, `curriculum_codesign`, `advisory_board`).

**Streaming format** for `POST /partnerships/targeted/stream`:
```
data: <NarrativeProposal JSON>\n\n
data: {"done": true}\n\n
```
On error: `data: {"error": "<message>"}\n\n`.

`GET /partnerships/landscape` reads the precomputed `PARTNERSHIP_ALIGNMENT` edge, which is materialized by `backend/partnerships/compute.py` during ingestion. `GET /partnerships/employer-pipeline` computes its result with a live traversal and does not depend on precomputed data. For the edge schema, see [Graph Model → Precomputed analytical edge](./graph-model.md#the-precomputed-analytical-edge).

## Strong Workforce

Defined in `backend/strong_workforce/api.py`, mounted at `/strong-workforce`. Both endpoints are AI-backed; the project generator streams its output.

| Method | Path | Purpose | Response model |
|---|---|---|---|
| `POST /strong-workforce/lmi-context` | Pre-fetch LMI demand/supply data for the SWP context panel (COE-grounded, non-streaming) | `LmiContext` |
| `POST /strong-workforce/project/stream` | Generate a full SWP project with sections streamed individually | text/event-stream |

**Request body** for both endpoints: `SwpProjectRequest` — carries the partnership proposal fields plus SWP-specific framing (`goal`, `metrics`, `apprenticeship`, `work_based_learning`). See `backend/strong_workforce/models.py` for the complete schema.

**Streaming format** for `POST /strong-workforce/project/stream`:
```
data: {"type": "lmi", "lmi_context": <LmiContext JSON>}\n\n
data: {"type": "section", "section": <SwpSection JSON>}\n\n
...
data: {"done": true}\n\n
```
The LMI context arrives first so the frontend can render the data panel immediately; subsequent `section` events arrive progressively as Claude finishes each section. On error: `data: {"error": "<message>"}\n\n`.

## How to regenerate this reference

FastAPI publishes the live OpenAPI schema at the /openapi.json URL and an interactive Swagger UI at /docs when the backend is running. This document is a static mirror of those routes, maintained in sync via the documentation audit (`tools/docs-audit/checks/api_endpoints.py`), which verifies every endpoint cited above against the actual router decorators in each feature's `api.py`. If this page drifts, the CI audit check fails.
