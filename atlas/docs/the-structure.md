# The atlas structure

The atlas is the Kallipolis frontend: a Next.js application that surfaces the two scales of the Atlas described in [`docs/product/the-atlas.md`](../../docs/product/the-atlas.md) — the College Atlas for a single institution, the State Atlas for the California community college system. This document is the forward-looking reference for how the atlas code is organized, why it is organized that way, and what rules keep it coherent as it grows.

## The essence

The atlas is organized **feature-primary**. Each ontology unit and each atlas scale owns a directory that holds all of the code about it — components, types, API client, supporting files — regardless of what kind of code it is. Cross-cutting infrastructure that is not owned by any single feature lives in a small number of purpose-named shared directories. The layer-primary split between `components/` and `lib/` that the atlas used to have is gone; a single feature is no longer scattered across four locations to be assembled by the reader.

The layout mirrors the backend's feature-primary layout (see [`backend/docs/structure-refactor.md`](../../backend/docs/structure-refactor.md)) so the two halves of the repository speak the same organizational language. A single product doc like [`docs/product/students.md`](../../docs/product/students.md) maps in one hop to `backend/students/` on the backend side and `atlas/college-atlas/students/` on the frontend side.

## Principles

1. **Feature-primary over layer-primary.** Organize by what the code is about (a unit, a scale), not by what kind of code it is (component, type, API client). Layer-primary layouts hide scope behind generic names and scatter single features across multiple locations.

2. **One-hop doc-to-code.** Every product doc maps to exactly one code location. A reader or an agent who understands the ontology finds the code without a second search.

3. **Shared infrastructure lives in small, purpose-named dirs.** Not a catch-all `shared/` or `utils/`. Each cross-cutting directory — `scene/`, `ui/`, `auth/`, `config/` — earns its name by having a single, defensible purpose.

4. **Uniform internal file patterns.** Every form folder under `college-atlas/` has the same shape: `<Form>View.tsx`, optional row components, `types.ts`, `api.ts`. An agent or reader who knows one feature knows them all.

5. **Orchestrators stay thin.** `app/` contains Next.js routes only. Route files import from feature folders and compose them; they do not own feature logic.

6. **URL surface matches feature names.** Atlas scales map to top-level routes (`/[collegeId]`, `/state`). Backend URL prefixes match feature names (`/students`, `/courses`, `/occupations`, `/employers`, `/partnerships`, `/strong-workforce`), so API calls from any feature's `api.ts` speak the same vocabulary as the folder it lives in.

## Folder contract

### `app/`

Next.js App Router routes. The only layer-primary folder at the top level of `atlas/`, imposed by the framework. Contains `[collegeId]/page.tsx` (College Atlas entry), `state/page.tsx` (State Atlas entry), `(auth)/` (login and register route group), `api/auth/` (Next.js API routes for auth), and the root `layout.tsx` and `page.tsx`. Route files are thin orchestrators that import feature components; they do not contain feature logic.

### `college-atlas/`

The College Atlas scale. Top-level files:

- `CollegeAtlasCanvas.tsx` — the six-form home scene canvas component.
- `scene.ts` — the scene configuration: `FormKey`, `FORM_NAMES`, `ALL_FORM_KEYS`, and the six forms' positions in 3D space. This file enumerates every form because the home scene assembles all six; it is the only place the six-form set is declared.

Each of the six forms has its own subfolder with the same internal layout:

- `<Form>View.tsx` — the main view component rendered when a user focuses on the form.
- Supporting components specific to the form (`StudentRow.tsx`, `ProposalCard.tsx`, etc.).
- `types.ts` — TypeScript types for the feature's domain.
- `api.ts` — API client functions and response types for the feature's backend endpoints.

The six form folders map to product docs:

| Folder | Product doc |
|---|---|
| `college-atlas/students/` | [`docs/product/students.md`](../../docs/product/students.md) |
| `college-atlas/courses/` | [`docs/product/courses.md`](../../docs/product/courses.md) |
| `college-atlas/occupations/` | [`docs/product/occupations.md`](../../docs/product/occupations.md) |
| `college-atlas/employers/` | [`docs/product/employers.md`](../../docs/product/employers.md) |
| `college-atlas/partnerships/` | [`docs/product/partnerships.md`](../../docs/product/partnerships.md) |
| `college-atlas/strong-workforce/` | [`docs/product/strong-workforce.md`](../../docs/product/strong-workforce.md) |

### `state-atlas/`

The State Atlas scale. Contains:

- `StateAtlas.tsx` — the top-level component for the State Atlas route.
- `CaliforniaMap.tsx` — the `react-simple-maps` California rendering.
- `californiaColleges.ts` — the canonical list of California community colleges and regional metadata.

The State Atlas is smaller than the College Atlas today because it has no per-feature subfolders; the map is the only surface. If the State Atlas grows features later, they should live in subfolders following the `college-atlas/` pattern.

### `scene/`

3D infrastructure. Contains:

- `engine.ts` — the generic `buildScene` function and Three.js helpers. Not specific to any scene.
- `forms/` — the six platonic geometric primitives (`mortarboard.ts`, `book.ts`, `chainlink.ts`, `hardhat.ts`, `skyscraper.ts`, `dumbbell.ts`). Each exports a factory that returns a Three.js group.

The `scene/` folder is 3D-only. Nothing in it knows about Kallipolis features, backends, or product concerns. It is reusable infrastructure that happens to be used by the College Atlas today.

### `ui/`

UI primitives used across the atlas. Contains `AtlasHeader.tsx`, `QueryShell.tsx`, `EntityScrollList.tsx`, `KallipolisBrand.tsx`, `Badge.tsx`, `Button.tsx`, `Card.tsx`, `DataCitation.tsx`, `LoadingDots.tsx`, `RisingSun.tsx`, `ColumnHeaders.tsx`, and `PageTransition.tsx`.

The `ui/` folder contains primitives only. A component lives here if and only if it is feature-agnostic — if it could be used by any feature without modification. Feature-specific row components (`StudentRow`, `DepartmentRow`, `OccupationRow`) live in their feature folders, not in `ui/`.

### `auth/`

Cross-cutting auth infrastructure. Contains the JWT and storage library (`jwt.ts`, `storage.ts`, `storage-kv.ts`, `storage-json.ts`, `crypto.ts`, `types.ts`) and the auth UI forms (`LoginForm.tsx`, `RegisterForm.tsx`, `LogoutButton.tsx`, `CollegeSelect.tsx`, `AtlasMenu.tsx`).

Auth is a cross-cutting concern because every route under `/` is gated by the session cookie verified in `middleware.ts`. The auth folder holds both the library layer and the UI layer together because neither is meaningful without the other.

### `config/`

Static configuration consumed across the atlas. Contains `schoolConfig.ts` (per-college branding, names, and color schemes), `collegeAtlasConfigs.ts` (the `getCollegeAtlasConfig` lookup function), and `collegeColors.generated.ts` (the generated color map).

Config files contain data and simple lookups, not behavior. Anything stateful or side-effecting belongs elsewhere.

### `api.ts`

The root `api.ts` holds one export: the `API_BASE` constant resolved from `NEXT_PUBLIC_API_URL` or falling back to `http://localhost:8000`. Every feature's `api.ts` imports `API_BASE` from this root. No other shared API logic lives here; if a helper becomes shared across features, it earns its own file rather than accreting in the root.

## Cross-feature dependencies

The only allowed cross-feature dependency is **`strong-workforce/` → `partnerships/`**, one-way, at two touch points:

1. **Shared proposal evidence types.** `strong-workforce/api.ts` type-imports `ApiOccupationEvidence`, `ApiCourseEvidence`, `ApiDepartmentEvidence`, `ApiStudentEvidence`, and `ApiProposalJustification` from `partnerships/api.ts`. A SWP project application is the *fund* stage of a discovered partnership; it consumes the evidence that `partnerships/` produces.

2. **Reading saved partnership proposals.** `strong-workforce/StrongWorkforceView.tsx` reads `getSavedProposals` and `SavedProposal` from `partnerships/savedProposals.ts` so that the SWP builder can pick up a previously saved partnership and turn it into a funding application.

Both touch points are read-only from the strong-workforce side — `partnerships/` is never a consumer of `strong-workforce/`. This mirrors the backend's `strong_workforce.generate` → `partnerships.generate` direction.

Saved SWP projects live in their own module at `strong-workforce/savedSwpProjects.ts` alongside their feature, so `partnerships/` has no reason to know about `ApiSwpProject` or any SWP-specific persistence.

All features can freely import from `ui/`, `config/`, `auth/`, and `scene/`. These are cross-cutting infrastructure folders; importing from them is the normal case.

## Anti-patterns

These are the patterns the layout exists to prevent. Encountering one is a sign that something is being pushed back toward the layer-primary mistake the refactor corrected.

**Do not create a `shared/` folder.** "Shared" folders accumulate things that are not really shared — cross-cutting primitives and feature-specific helpers end up mixed together. Either a component is a true primitive (belongs in `ui/`) or it belongs to a specific feature (belongs in that feature's folder).

**Do not put feature-specific types in `ui/` or `config/`.** UI primitives are type-generic; feature types belong in the feature's `types.ts` or `api.ts`.

**Do not reach into another feature's internals.** A cross-feature import should only go through the other feature's `api.ts` (which is the feature's public interface). Importing internal components, helpers, or local types from another feature creates implicit coupling that breaks the one-folder-per-feature guarantee.

**Do not introduce a new cross-feature dependency without moving the shared thing.** If feature X needs something from feature Y, the preferred fix is to move the shared thing to `config/` (if it is static data), `ui/` (if it is a UI primitive), or the more-dependent feature's folder (if it is a type with a clear primary owner). Only escalate to a cross-feature import if none of those fit.

**Do not duplicate API client logic across features.** Each feature's `api.ts` imports `API_BASE` from the root `api.ts` and calls `fetch` directly. If a shared helper (retry logic, auth headers, SSE parsing) becomes necessary across multiple features, it earns its own file under an appropriate shared folder — not a silent duplication.

**Do not create a layer-primary sub-structure inside a feature folder.** A feature folder should not grow into `students/components/`, `students/types/`, `students/api/`. The feature folder is the feature; its internal files are named for their role (`<Form>View.tsx`, `types.ts`, `api.ts`), not grouped by layer.
