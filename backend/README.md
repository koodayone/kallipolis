# backend

Kallipolis backend. This file is a navigation aid — anything substantive
about the system's shape lives under [`docs/`](../docs/README.md) and is
enforced by the documentation audit. Read [`docs/README.md`](../docs/README.md)
for the product and architecture story.

## Layout

The backend is **feature-primary**: each ontology unit owns a directory
containing everything about that unit — routes, queries, models, ingestion.
Cross-unit infrastructure lives in `ontology/` and `llm/`.

```
backend/
├── main.py                FastAPI entry point; mounts per-feature routers
│
├── ontology/              Cross-unit schema and reference data
│   ├── schema.py          Neo4j driver, constraints, init
│   ├── skills.py          Unified skills taxonomy
│   ├── regions.py         College ↔ Metro ↔ COE region mapping
│   ├── supply.py          COE supply/demand lookups
│   ├── mcf_lookup.py      Master Course File TOP6 resolution
│   ├── crosswalks.py      SOC/NAICS/CIP/TOP crosswalks
│   ├── calibrations/      Per-college TOP code calibration data
│   └── mastercoursefiles/ Institutional course reference data
│
├── llm/                   Shared LLM infrastructure
│   └── query_engine.py    NL → Cypher with safety gate
│
├── students/              ↔ docs/product/students.md
├── courses/               ↔ docs/product/courses.md
├── occupations/           ↔ docs/product/occupations.md
├── employers/             ↔ docs/product/employers.md
├── partnerships/          ↔ docs/product/partnerships.md  (unit of action)
├── strong_workforce/      ↔ docs/product/strong-workforce.md  (unit of action)
│
├── pipeline/              Orchestration + cross-cutting prep scripts
│   ├── run.py             Academic pipeline entry point
│   ├── reload.py          Reset + reingest
│   └── ...                Calibration and taxonomy prep utilities
│
├── tests/
│   ├── unit/              Fast, no I/O, no external deps
│   └── integration/       Neo4j + LLM-coupled scripts
│
├── scripts/               One-off maintenance utilities
└── docs/                  Backend-specific internal notes
```

## Feature-dir conventions

Each feature directory follows the same file shape. Not every feature has
every file, but when a file exists, its name means the same thing:

```
<feature>/
├── models.py       Pydantic schemas for this feature
├── api.py          FastAPI routes for this feature
├── query.py        LLM-backed retrieval (for units of analysis)
├── generate.py     LLM-backed generation (for units of action)
├── load.py         Neo4j persistence for ingested data
├── <source>.py     External data fetch (scrapers, parsers)
└── *.json, *.csv   Feature-specific reference data
```

## Dependency direction

```
ontology/  →  llm/  →  features  →  main.py
                            ↑
                        pipeline/
```

Features may import from `ontology/` and `llm/`. They may import from other
features only along a DAG — for example, `strong_workforce/` depends on
`partnerships/`, not the other way around. `pipeline/` orchestrates ingestion
and imports from features; features never import from `pipeline/`.

## Running

```bash
# Unit tests (fast, no dependencies)
cd backend && python3 -m pytest tests/unit/

# Docs audit (stdlib only, verifies this README too)
python3 tools/docs-audit/audit.py

# Full server (requires Neo4j + ANTHROPIC_API_KEY + GEMINI_API_KEY)
cd backend && uvicorn main:app --reload

# Ingestion pipeline
cd backend && python3 -m pipeline.run --college foothill
```

## Where to go next

- **Product docs** — [`docs/product/`](../docs/product/): what each ontology unit *is*, not just what the code does.
- **System architecture** — [`docs/architecture/system-overview.md`](../docs/architecture/system-overview.md) and [`docs/architecture/graph-model.md`](../docs/architecture/graph-model.md).
- **Pipeline internals** — [`docs/pipeline/`](../docs/pipeline/).
- **Why this layout** — [`backend/docs/structure-refactor.md`](../backend/docs/structure-refactor.md) is the migration plan behind the feature-primary refactor.
