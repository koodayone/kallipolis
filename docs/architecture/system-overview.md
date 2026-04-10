# System Overview

*Audience: engineers extending or modifying Kallipolis. Assumes familiarity with Next.js, Python, and graph databases.*

Kallipolis is composed of three applications and one database, orchestrated by Docker Compose for the persistent services and run independently for the frontends.

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

Everything in Kallipolis revolves around a single Neo4j graph. The graph holds eight node types and roughly eleven relationship types, encoding the curriculum side and the industry side bridged by skills.

**Curriculum side.** `College → Department → Course → Skill ← Student`. A college offers departments, which contain courses, which develop skills. Students enroll in courses and inherit the skills those courses develop.

**Industry side.** `Region ← College/Employer, Region → Occupation → Skill, Employer → Occupation`. Regions demand occupations with wage and employment metadata. Occupations require skills. Employers hire for occupations.

**The bridge.** `Skill` is the same node type on both sides. A skill that appears in `(:Course)-[:DEVELOPS]->(:Skill)` and `(:Occupation)-[:REQUIRES_SKILL]->(:Skill)` is a "bridge skill" — it connects what colleges teach to what regional employers need. Partnership opportunities are computed by traversing these bridges.

For the full schema, see [Graph Model](./graph-model.md) *(draft)*.

## The AI surface

Kallipolis calls two LLM providers, each for a distinct role:

**Claude** handles linguistic operations against existing data. Five system prompts translate natural language questions into validated Cypher (`backend/workflows/query_engine.py`). Two narrative generators write partnership proposals and SWP project sections (`backend/workflows/partnerships.py`, `backend/workflows/swp.py`). Both run with `claude-sonnet-4-6` and use server-sent events for streaming output.

**Gemini** handles data extraction during the ETL pipeline. Course extraction from PDF catalogs, skill taxonomy mapping, occupation-skill assignment, and employer name cleanup all run on `gemini-2.5-flash`.

The split is deliberate. Claude is asked to reason about institutional context — gaps, alignments, narratives, voice. Gemini is asked to do high-volume structured extraction from documents. Neither model crosses into the other's role.

## The three API surfaces

The backend exposes three routers, each scoped to a domain:

| Router | Path prefix | Purpose |
|---|---|---|
| `ontology` | `/ontology/*` | College, departments, courses, students |
| `labor_market` | `/labor-market/*` | Occupations, employers, partnership landscape |
| `workflows` | `/workflows/*` | Partnership proposals (streaming), SWP builder (streaming) |

Each ontology and labor market router exposes both **direct query endpoints** (deterministic Cypher) and **NL query endpoints** (Claude-generated Cypher with validation). Workflows are exclusively AI-driven and stream their output.

For the complete endpoint list, see [API Reference](./api-reference.md) *(draft)*.

## Authentication and scoping

Authentication lives in the atlas, not the backend. The atlas issues JWTs via Next.js API routes (`atlas/app/api/auth/*`), stores them in HttpOnly cookies, and validates them in middleware. The backend trusts the atlas — it does not verify tokens itself. All backend endpoints require a `college` query parameter, and all Cypher queries are scoped by that parameter. There is no user-level authorization in the backend; college scoping is the only access boundary.

For the auth flow, see [Authentication](./authentication.md) *(draft)*.

## Streaming

Two endpoints stream their output to the atlas using server-sent events:

- `POST /workflows/partnerships/targeted/stream` — emits the proposal as Claude generates it
- `POST /workflows/swp/project/stream` — emits SWP sections incrementally with brace-depth JSON parsing to extract complete section objects mid-stream

Both use FastAPI's `StreamingResponse` with `text/event-stream`. The atlas reads them via the Fetch API's `ReadableStream` reader.

For the streaming protocol details, see [Streaming](./streaming.md) *(draft)*.

## What lives where

```
kallipolis/
├── app/, components/, lib/      # Landing page (port 3000)
├── atlas/                       # Atlas (port 3001) — full app
├── backend/                     # FastAPI + pipeline + graph schema
│   ├── api/                     # FastAPI routers
│   ├── workflows/               # Business logic and AI orchestration
│   ├── ontology/                # Neo4j schema and driver
│   ├── pipeline/                # ETL ingestion (per-college and per-region)
│   ├── models/                  # Pydantic data models
│   └── main.py                  # FastAPI entry point
├── docs/                        # This documentation
└── docker-compose.yml           # Neo4j + backend orchestration
```

The landing page lives at the repo root because it was the first thing built. The atlas was added later as a sibling directory rather than absorbed into the root app.

## Where to go next

- [Graph Model](./graph-model.md) — The full Neo4j schema *(draft)*
- [API Reference](./api-reference.md) — All endpoints *(draft)*
- [AI Integration](./ai-integration.md) — Where and why each LLM is called *(draft)*
- [Pipeline Overview](../pipeline/) — How data enters the graph
