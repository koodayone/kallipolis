# System Overview

Kallipolis is composed of three applications and one database. The two frontends run independently as Next.js apps; the backend and the database are orchestrated together via Docker Compose. This document describes the system at the level a reader needs to hold its shape in their head — what the components are, how they relate, and where the substantive engineering work lives.

## The four components

| Component | Tech | Port | Purpose |
|---|---|---|---|
| Landing page | Next.js 16 + React 19 | 3000 | Marketing site, public entry point |
| Atlas | Next.js 16 + React 19 + Three.js | 3001 | Authenticated interactive 3D visualization |
| Backend | FastAPI + Python | 8000 | API, AI orchestration, Neo4j gateway |
| Database | Neo4j 5.18 | 7687 (bolt), 7474 (browser) | Graph storage |

The landing page and atlas are independent Next.js apps. They share no code and run on different ports. The backend serves both indirectly — only the atlas calls it.

```
                    ┌──────────────────┐
                    │ User (browser)   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌────────────────┐            ┌────────────────┐
     │ Landing page   │            │ Atlas          │
     │ :3000          │            │ :3001          │
     └────────────────┘            └────────┬───────┘
                                            │ HTTPS
                                            ▼
                                   ┌────────────────┐
                                   │ Backend API    │
                                   │ FastAPI :8000  │
                                   └────┬───┬───┬───┘
                                        │   │   │
                            ┌───────────┘   │   └─────────┐
                            ▼               ▼             ▼
                   ┌────────────────┐  ┌─────────┐  ┌──────────┐
                   │ Neo4j :7687    │  │ Claude  │  │ Gemini   │
                   │ (graph)        │  │ API     │  │ API      │
                   └────────────────┘  └─────────┘  └──────────┘
```

## The graph at the center

Everything in Kallipolis revolves around a single Neo4j graph. The graph holds seven node types and nine directional relationship pairings (built from eight unique relationship type names, with `IN_MARKET` overloaded across College→Region and Employer→Region), encoding the curriculum side and the industry side of the workforce development equation, bridged through the institutional TOP-CIP-SOC crosswalk.

**Curriculum side.** `College → Department → Course ← Student`. A college offers departments, which contain courses. Students enroll in courses.

**Industry side.** `Region ← College/Employer, Region → Occupation, Employer → Occupation`. Regions demand occupations with wage and employment metadata. Employers hire for occupations.

**The bridge.** `Course → PREPARES_FOR → Occupation` is the institutional bridge edge. It is materialized at curriculum-load time from each course's TOP code via the Chancellor's Office TOP-CIP and BLS/NCES CIP-SOC crosswalks, and it carries `via_top` as an audit-trail property. Partnership opportunities are computed by traversing this bridge between an employer's hires occupations and the college's PREPARES_FOR-aligned courses.

For the full schema, see [Graph Model](./graph-model.md).

## The AI surface

Kallipolis calls two LLM providers, each for a distinct role.

**Claude** handles linguistic operations against existing data. Five system prompts translate natural language questions into validated Cypher (`backend/llm/query_engine.py`). The proposal endpoint uses server-sent events for streaming output, but the proposal narrative itself is composed deterministically from templates over structured graph evidence — no Claude call at composition time.

**Gemini** handles data extraction during the ETL pipeline. Course extraction from PDF catalogs and employer name cleanup with occupation assignment both run on Gemini.

The split is deliberate. Claude is asked to reason about institutional context — translating questions into Cypher against the graph schema. Gemini is asked to do high-volume structured extraction from documents. Neither model crosses into the other's role.

For the full treatment of where each model is called and why, see [AI Integration](./ai-integration.md).

## The five API surfaces

The backend exposes one router per ontology unit, each scoped to a single conceptual noun. The four units of analysis each have a router that exposes both deterministic retrieval and Claude-generated Cypher retrieval. The unit of action has a router that exposes LLM-backed proposal generation, streamed via server-sent events.

| Router | Path prefix | Purpose |
|---|---|---|
| `students` | `/students/*` | Student roster and detail, NL student query |
| `courses` | `/courses/*` | College and department structure, course listing, NL course query |
| `occupations` | `/occupations/*` | Labor market overview, occupation detail, NL occupation query |
| `employers` | `/employers/*` | Employer listing and detail, NL employer query |
| `partnerships` | `/partnerships/*` | Partnership landscape (read), NL partnership query, targeted proposal generation (streaming) |

The four analysis-unit routers (`students`, `courses`, `occupations`, `employers`) expose both direct query endpoints (deterministic Cypher) and an NL `/query` endpoint (Claude-generated Cypher with a safety gate). The action-unit router (`partnerships`) is AI-driven and streams its output.

For the full endpoint catalog — methods, paths, request shapes, response shapes — see [API Reference](./api-reference.md).

## Streaming

All endpoints are request-response; the Partnerships flow is fast enough end-to-end that no streaming is needed. The per-(college, SOC) opportunity report is composed deterministically at request time and returned as a single JSON payload.

## Authentication and scoping

The preview deployment ships without authentication. The atlas serves the State Atlas at the root route; any visitor can navigate to any college's College Atlas and exercise the same flows, including the streaming generation endpoints. All backend endpoints require a `college` query parameter, and Cypher queries in `backend/ontology/schema.py` and each feature's `query.py` are scoped by that parameter. College scoping is the only access boundary, and it is currently enforced by the atlas passing the correct college name — the backend trusts the origin.

This is appropriate for the product's current stage. The preview is a pre-pilot GTM instrument operating on entirely public data (DataMart, Centers of Excellence, EDD, college catalogs), so the threat model has no adversarial component yet. Persistence is deferred alongside authentication: every visitor sees the same deterministic surfaces, and the Partnerships node ships in identification mode (no per-user state). When the first pilot signs, authentication, server-side persistence, and managed-entity features (partnership status tracking, history, follow-up) return together as additive layers on top of the same ontology — activation is additive rather than a refactor.

See [Deployment](./deployment.md) for how the preview topology operationalizes this posture.

## What lives where

The backend is **feature-primary**: each ontology unit owns a directory containing routes, queries, models, and ingestion code for that unit. Cross-unit infrastructure lives in `ontology/` (graph schema, shared reference data, calibrations) and `llm/` (the NL-to-Cypher engine). `pipeline/` is a thin orchestration layer that imports from features, not the other way around.

```
kallipolis/
├── app/, components/, lib/      # Landing page (port 3000)
├── atlas/                       # Atlas (port 3001) — full app
├── backend/
│   ├── main.py                  # FastAPI entry point; mounts per-feature routers
│   ├── ontology/                # Neo4j schema, driver, regions, supply/demand,
│   │                            #   institutional TOP-CIP-SOC crosswalks, calibrations
│   ├── llm/                     # Shared NL-to-Cypher engine with safety gate
│   ├── students/                # ↔ docs/product/students.md
│   ├── courses/                 # ↔ docs/product/courses.md
│   ├── occupations/             # ↔ docs/product/occupations.md
│   ├── employers/               # ↔ docs/product/employers.md
│   ├── partnerships/            # ↔ docs/product/partnerships.md (unit of action)
│   ├── pipeline/                # Ingestion orchestration + calibration prep
│   ├── tests/unit/              # Fast, no I/O unit suite (CI-gated)
│   └── tests/integration/       # Neo4j + LLM-coupled scripts (local only)
├── docs/                        # This documentation
└── docker-compose.yml           # Neo4j + backend orchestration
```

Each feature directory follows the same file shape: `models.py`, `api.py`, `query.py` (analysis units) or `generate.py` (action units), `load.py` (when ingested), plus feature-specific scrapers or reference data. For the full per-directory conventions, see [`backend/README.md`](../../backend/README.md).

The landing page lives at the repository root because it was the first thing built. The atlas was added later as a sibling directory rather than being absorbed into the root app, which keeps the two frontends cleanly separated.

## Where to go next

- [Graph Model](./graph-model.md) — The full Neo4j schema, constraints, and the relationship types that encode the supply-demand chain
- [AI Integration](./ai-integration.md) — Where and why each LLM is called, and what the constraints on each call are
- [Deployment](./deployment.md) — How this system ships to production: Cloudflare Pages, a GCP VM, Caddy-terminated TLS, nightly backups to Cloud Storage
- [Pipeline Overview](../pipeline/) — How institutional data enters the graph
