# atlas

Kallipolis atlas. This file is a navigation aid — anything substantive
about the system's shape lives under [`docs/`](../docs/README.md) and
[`atlas/docs/the-structure.md`](./docs/the-structure.md), and is enforced
by the documentation audit. Read [`docs/product/the-atlas.md`](../docs/product/the-atlas.md)
for the product story: what the Atlas is, why it operates at two scales,
and how it relates to the ontology beneath it.

## Layout

The atlas is **feature-primary**: each ontology form and each atlas scale
owns a directory containing everything about it — components, types, API
client, supporting files. Cross-cutting infrastructure lives in small
purpose-named folders (`scene/`, `ui/`, `auth/`, `config/`).

```
atlas/
├── app/                        Next.js App Router entry points
│   ├── [collegeId]/
│   │   ├── layout.tsx          Persistent 3D canvas + scene pause logic
│   │   ├── page.tsx            Home: six-form scene + labels + header
│   │   ├── students/page.tsx   Thin route wrappers for the six form views
│   │   ├── courses/page.tsx
│   │   ├── occupations/page.tsx
│   │   ├── employers/page.tsx
│   │   ├── partnerships/page.tsx
│   │   └── strong-workforce/page.tsx
│   ├── state/page.tsx          State Atlas route
│   ├── (auth)/                 Login / register route group
│   └── api/auth/               Next.js API routes for session cookies
│
├── college-atlas/              ↔ docs/product/the-atlas.md (College Atlas)
│   ├── CollegeAtlasCanvas.tsx  The Three.js canvas component
│   ├── scene.ts                FormKey, FORM_NAMES, six-form scene config
│   ├── homeSceneContext.ts     Shared projected positions + hover state
│   ├── students/               ↔ docs/product/students.md
│   ├── courses/                ↔ docs/product/courses.md
│   ├── occupations/            ↔ docs/product/occupations.md
│   ├── employers/              ↔ docs/product/employers.md
│   ├── partnerships/           ↔ docs/product/partnerships.md
│   └── strong-workforce/       ↔ docs/product/strong-workforce.md
│
├── state-atlas/                ↔ docs/product/the-atlas.md (State Atlas)
│   ├── StateAtlas.tsx
│   ├── CaliforniaMap.tsx
│   └── californiaColleges.ts
│
├── scene/                      3D infrastructure (cross-feature, 3D only)
│   ├── engine.ts               Generic buildScene + Three.js helpers
│   └── forms/                  Six platonic geometric primitives
│
├── ui/                         UI primitives (feature-agnostic)
├── auth/                       JWT + session storage + auth UI forms
├── config/                     Static configuration (per-college branding)
│
├── api.ts                      Shared API_BASE constant
├── proxy.ts                    JWT cookie verification (Next.js 16 proxy convention)
└── docs/                       Atlas-specific internal notes
```

## Feature folder conventions

Each folder under `college-atlas/` follows the same internal shape. Not
every feature needs every file, but when a file exists its name means the
same thing:

```
college-atlas/<form>/
├── <Form>View.tsx     Main component rendered by the form's route
├── <Form>Row.tsx      Optional per-row component (students, courses, …)
├── types.ts           TypeScript types for the feature's domain
└── api.ts             Feature's API client + response types
```

Supporting components specific to one feature (e.g. `ProposalCard.tsx`,
`SwpArtifact.tsx`) live in that feature's folder, not in `ui/`.

## Cross-feature dependencies

```
scene/, ui/, auth/, config/  →  features  →  app/
                                    ↑
                              partnerships (evidence types)
                                    ↓
                              strong-workforce
```

Features may freely import from `scene/`, `ui/`, `auth/`, and `config/`.
The only allowed cross-feature import is `strong-workforce/` → `partnerships/`,
one-way, for shared proposal evidence types and for reading saved partnership
proposals. A SWP project is the *fund* stage of a discovered partnership, so
it consumes partnership output. This mirrors the backend's
`strong_workforce.generate` → `partnerships.generate` direction.

See [`atlas/docs/the-structure.md`](./docs/the-structure.md) for the full
dependency contract and the anti-patterns the layout exists to prevent.

## Running

```bash
# Local dev (port 3001, requires backend running on :8000)
cd atlas && npm run dev

# Production build and start
cd atlas && npm run build && npm run start

# Type check (no emit)
cd atlas && npx tsc --noEmit

# Unit tests (Vitest, pure-logic only)
cd atlas && npm test
cd atlas && npm run test:watch            # interactive watch mode
cd atlas && npm test -- --reporter=verbose  # list every describe/it — the "what's covered?" view

# Docs audit (verifies this README's code path references)
python3 tools/docs-audit/audit.py
```

## Where to go next

- **Product docs** — [`docs/product/`](../docs/product/): what each ontology unit *is*, not just what the code does. Start with [`the-atlas.md`](../docs/product/the-atlas.md) for the two-scale framing.
- **Structural reference** — [`atlas/docs/the-structure.md`](./docs/the-structure.md): the principles behind this layout, the folder contract, and the anti-patterns it exists to prevent. Read this before adding, moving, or reorganizing files under `atlas/`.
- **Testing reference** — [`atlas/docs/testing.md`](./docs/testing.md): the test suite's philosophy, file organization, naming convention, and the JSDoc coverage header convention the docs audit enforces. Read this before adding a new test file.
- **Agent entry point** — [`atlas/CLAUDE.md`](./CLAUDE.md): short pointer-style directive that routes agents to `the-structure.md` at decision points.
- **Backend counterpart** — [`backend/README.md`](../backend/README.md): the frontend and backend share the same feature-primary vocabulary. A product doc maps in one hop to both sides.
- **System architecture** — [`docs/architecture/system-overview.md`](../docs/architecture/system-overview.md): three apps, one graph, streaming and auth patterns.
