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

Everything in Kallipolis revolves around a single Neo4j graph. The graph holds eight node types and ten directional relationship pairings (built from nine unique relationship type names, with `IN_MARKET` overloaded across College→Region and Employer→Region), encoding the curriculum side and the industry side of the workforce development equation, bridged through skills.

**Curriculum side.** `College → Department → Course → Skill ← Student`. A college offers departments, which contain courses, which develop skills. Students enroll in courses and inherit the skills those courses develop.

**Industry side.** `Region ← College/Employer, Region → Occupation → Skill, Employer → Occupation`. Regions demand occupations with wage and employment metadata. Occupations require skills. Employers hire for occupations.

**The bridge.** `Skill` is the same node type on both sides. A skill that appears in `(:Course)-[:DEVELOPS]->(:Skill)` and `(:Occupation)-[:REQUIRES_SKILL]->(:Skill)` is a bridge skill. It connects what colleges teach to what regional employers need, and partnership opportunities are computed by traversing these bridges.

For the full schema, see [Graph Model](./graph-model.md).

## The AI surface

Kallipolis calls two LLM providers, each for a distinct role.

**Claude** handles linguistic operations against existing data. Five system prompts translate natural language questions into validated Cypher (`backend/llm/query_engine.py`). Two narrative generators write partnership proposals and SWP project sections (`backend/partnerships/generate.py`, `backend/strong_workforce/generate.py`). Both use server-sent events for streaming output.

**Gemini** handles data extraction during the ETL pipeline. Course extraction from PDF catalogs, skill taxonomy mapping, occupation-skill assignment, and employer name cleanup all run on Gemini.

The split is deliberate. Claude is asked to reason about institutional context — gaps, alignments, narratives, voice. Gemini is asked to do high-volume structured extraction from documents. Neither model crosses into the other's role.

For the full treatment of where each model is called and why, see [AI Integration](./ai-integration.md).

## The six API surfaces

The backend exposes one router per ontology unit, each scoped to a single conceptual noun. The four units of analysis each have a router that exposes both deterministic retrieval and Claude-generated Cypher retrieval. The two units of action each have a router that exposes LLM-backed proposal generation, streamed via server-sent events.

| Router | Path prefix | Purpose |
|---|---|---|
| `students` | `/students/*` | Student roster and detail, NL student query |
| `courses` | `/courses/*` | College and department structure, course listing, NL course query |
| `occupations` | `/occupations/*` | Labor market overview, occupation detail, NL occupation query |
| `employers` | `/employers/*` | Employer listing and detail, NL employer query |
| `partnerships` | `/partnerships/*` | Partnership landscape (read), NL partnership query, targeted proposal generation (streaming) |
| `strong_workforce` | `/strong-workforce/*` | LMI context, SWP project generation (streaming) |

The four analysis-unit routers (`students`, `courses`, `occupations`, `employers`) expose both direct query endpoints (deterministic Cypher) and an NL `/query` endpoint (Claude-generated Cypher with a safety gate). The two action-unit routers (`partnerships`, `strong_workforce`) are AI-driven and stream their output.

For the full endpoint catalog — methods, paths, request shapes, response shapes — see [API Reference](./api-reference.md).

## Streaming

Two endpoints stream their output to the atlas using server-sent events: the partnership proposal generator and the SWP project builder. Both use FastAPI's `StreamingResponse` with `text/event-stream`. The atlas reads them via the Fetch API's `ReadableStream` reader. The SWP stream uses brace-depth JSON parsing to extract complete section objects mid-stream, so each section can be displayed as soon as the model finishes generating it rather than waiting for the entire response. This is why a coordinator using the strong workforce flow sees sections appear progressively rather than all at once.

## Authentication and scoping

The preview deployment ships without authentication. The atlas serves the State Atlas at the root route; any visitor can navigate to any college's College Atlas and exercise the same flows, including the streaming generation endpoints. All backend endpoints require a `college` query parameter, and Cypher queries in `backend/ontology/schema.py` and each feature's `query.py` are scoped by that parameter. College scoping is the only access boundary, and it is currently enforced by the atlas passing the correct college name — the backend trusts the origin.

This is appropriate for the product's current stage. The preview is a pre-pilot GTM instrument operating on entirely public data (DataMart, Centers of Excellence, EDD, college catalogs), so the threat model has no adversarial component yet. Persistence is deferred alongside authentication: saves are disabled in the preview with a tooltip directing prospects to contact for pilot activation, and in-session drafts live in React state only. When the first pilot signs, authentication, server-side saves, and per-user state return together. The code path for those features is intentionally present in skeleton form — `atlas/session/SessionDraftsContext.tsx` holds the session boundary, and the `NEXT_PUBLIC_AUTH_ENABLED` flag gates preview-specific UI — so activation is additive rather than a refactor.

See [Deployment](./deployment.md) for how the preview topology operationalizes this posture.

## What lives where

The backend is **feature-primary**: each ontology unit owns a directory containing routes, queries, models, and ingestion code for that unit. Cross-unit infrastructure lives in `ontology/` (graph schema, shared reference data, calibrations) and `llm/` (the NL-to-Cypher engine). `pipeline/` is a thin orchestration layer that imports from features, not the other way around.

```
kallipolis/
├── app/, components/, lib/      # Landing page (port 3000)
├── atlas/                       # Atlas (port 3001) — full app
├── backend/
│   ├── main.py                  # FastAPI entry point; mounts per-feature routers
│   ├── ontology/                # Neo4j schema, driver, unified skills taxonomy,
│   │                            #   regions, supply/demand, crosswalks, calibrations
│   ├── llm/                     # Shared NL-to-Cypher engine with safety gate
│   ├── students/                # ↔ docs/product/students.md
│   ├── courses/                 # ↔ docs/product/courses.md
│   ├── occupations/             # ↔ docs/product/occupations.md
│   ├── employers/               # ↔ docs/product/employers.md
│   ├── partnerships/            # ↔ docs/product/partnerships.md (unit of action)
│   ├── strong_workforce/        # ↔ docs/product/strong-workforce.md (unit of action)
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
