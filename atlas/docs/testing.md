# Atlas testing

This document is the contract for how tests are written and organized in the atlas. It is load-bearing for the test suite's legibility and for the docs audit that verifies it. Read this before adding a new test file, moving tests around, or changing the test conventions.

The atlas test suite exercises two layers. The first is pure logic — the `api.ts` clients, the `scene.ts` vocabulary, small extracted helpers like `buildSwpRequest.ts`. The second is component rendering — shared UI primitives under `ui/` (starting with `AtlasHeader`) tested with React Testing Library against happy-dom. It does not yet exercise the 3D scene, the backend, or full end-to-end flows.

## Philosophy

**Tests exercise units, not features.** A test file targets one exported function, one module, or one small cluster of related functions. A feature can have many test files, each focused. This keeps individual test files small and keeps the relationship between "what is this testing?" and "what does this file contain?" obvious from the filename alone.

**Test names read as specifications.** A reader skimming the test file or running `npm test -- --reporter=verbose` should see sentences describing what the unit does, not noun phrases describing what the test is. "Falls back to a Workforce default when the engagement type is unrecognized" is a specification. "Tests fallback" is not. The convention applies to both `describe` labels and `it` labels.

**Pure logic first, components second.** Anything that can be tested without React or a DOM is tested that way — it's faster, more stable, and the failure modes are unambiguous. Component tests exist for the second category of bug: user-visible regressions that pure logic cannot catch, like a missing button, a broken click handler, or a conditional slot that renders the wrong thing. Backend-integration and end-to-end tests remain deferred.

**Component tests assert behavior, not appearance.** Query the DOM by role, label, or accessible name — never by class name, CSS selector, or computed style. Interact via `@testing-library/user-event`, not synthetic events. Assert what a user would perceive: "a button with this label exists", "clicking it calls this handler", "this text is in the document". Do not assert font sizes, colors, pixel positions, or inline-style values. If you find yourself reaching for `getComputedStyle` or `toHaveStyle`, you are testing the wrong layer — that belongs in a visual regression tool, not Vitest.

## Framework

**Vitest** is the test runner. Jest-compatible API (`describe`, `it`, `expect`, `vi`), native TypeScript and ESM support, sub-second startup. The config lives at `atlas/vitest.config.ts` and uses the **happy-dom** environment so the same runner handles both pure-logic and component tests. Pure-logic tests don't pay a meaningful cost from the DOM environment — happy-dom is lazy and the suite still runs in well under a second.

Tests are picked up by the pattern `**/*.test.{ts,tsx}`, excluding `node_modules/` and `.next/`. A shared `atlas/test/setup.ts` runs before every test file; it imports `@testing-library/jest-dom/vitest` so matchers like `toBeInTheDocument` are available, and it registers an `afterEach` that calls React Testing Library's `cleanup` to unmount components between tests.

**Component test dependencies.** `@testing-library/react` (render, screen, queries), `@testing-library/user-event` (realistic user interactions), `@testing-library/jest-dom` (assertion matchers), and `happy-dom` (fast DOM implementation). All four are devDependencies on atlas.

## File organization

**Tests colocate with the source files they exercise.** A test for `buildSwpRequest.ts` lives at `buildSwpRequest.test.ts` in the same folder. This matches the feature-primary principle documented in [`the-structure.md`](./the-structure.md) — a feature's tests are part of the feature they exercise, not a centralized parallel tree. The backend chose a centralized `tests/unit/` layout because Python conventions lean that way; Vitest and the TypeScript ecosystem lean toward colocation.

Colocation has three concrete benefits. A reader looking at a feature folder sees which files have tests and which don't without navigating to a separate tree. An agent changing a file can find its test without a search. Moving or renaming a feature moves its tests atomically.

## Top-of-file JSDoc coverage header

**Every `.test.{ts,tsx}` file in the atlas begins with a JSDoc block that names the unit under test and lists the coverage areas.** This is the mechanism for per-feature legibility: a human can open a test file and read in plain language what it asserts, without running Vitest and without reading every `it` block.

The header has a fixed shape:

```ts
/**
 * Tests for <unit name> — <one-line description of what the unit does>.
 *
 * <optional: one or two paragraphs of context about why these tests
 * matter, what makes this unit worth guarding, what mocking pattern
 * is used, etc.>
 *
 * Coverage:
 *   - <first coverage area, phrased as an outcome>
 *   - <second coverage area>
 *   - <third coverage area>
 */
```

**The header is required.** The docs audit has a check (`atlas_test_headers`) that scans every atlas test file and fails if it is missing the `/**`-block opening or the `Coverage:` line. Missing headers block merge to `main`.

**Why the header matters when `describe`/`it` names already exist.** The test names tell you what a specific test asserts; the header tells you what the file as a whole guards. A reader skimming the suite wants "the buildSwpRequest test file covers the engagement-type default lookup and the request payload construction" as a single sentence, not as an inference from 15 individual test names. The header is the summary index; the test names are the line items.

**How to update it.** When you add a test that covers a new area, add a bullet to the Coverage list in the same commit. When you remove or refactor a test, update the list. Drift is possible — the audit only checks that the header exists, not that its contents match the tests — so the convention relies on author discipline at write time. Reviewers should reject test PRs where the Coverage list does not match what the tests assert.

## Test naming convention

- **`describe` labels name the unit or a logical grouping inside the unit.** Examples: `"buildSwpRequest"`, `"engagement-type defaults"`, `"request payload construction"`, `"getStudents"`.
- **`it` labels read as specifications.** A good `it` label reads naturally as the sentence "the unit ... when ...". Examples: `"applies internship defaults: Workforce goal, WBL true, apprenticeship false"`, `"passes through proposal fields verbatim into the request"`, `"throws a descriptive error when the response is not ok"`.
- **Avoid meta-phrasing.** `"tests that X"`, `"should X"`, and `"verifies X"` all add noise. Write the specification directly: `"X when Y"` or `"X with Y"`.

The goal is that `npm test -- --reporter=verbose` produces output a non-author can read to understand what the suite covers.

## Mocking

- **`fetch` is the only global routinely stubbed.** Use `vi.stubGlobal("fetch", mockFn)` and `vi.unstubAllGlobals()` in `afterEach`. See `college-atlas/students/api.test.ts` for the canonical pattern.
- **Import real modules, not mocks, for pure-logic tests.** `buildSwpRequest.test.ts` imports `buildSwpRequest` directly and builds plain-object fixtures.
- **Avoid `vi.mock` at module scope unless necessary.** It interacts badly with import hoisting and makes tests harder to read. Prefer explicit dependency injection where possible.

## Component testing conventions

Component tests live next to the component they cover, named `<Component>.test.tsx`. The same JSDoc coverage header and `describe`/`it` naming rules apply.

- **Query by role first.** `screen.getByRole("button", { name: "Back to College Atlas" })` is the canonical query. Fall back to `getByLabelText`, `getByText`, or `getByTestId` only when role-based queries don't fit. A `data-testid` is an escape hatch, not a default.
- **Interact via `userEvent`, not `fireEvent`.** `await userEvent.click(...)` simulates the realistic sequence of pointer and focus events a real click dispatches. Synthetic-event APIs skip that sequence and hide bugs.
- **Assert the user-perceived outcome.** "The button exists", "the handler was called", "the text is in the document". Do not assert inline style values, hex colors, pixel widths, or DOM structure that a user cannot perceive.
- **Use `cleanup` implicitly.** The shared `test/setup.ts` already calls `cleanup` after each test. Do not call `unmount()` manually unless you are testing unmount behavior specifically.
- **Mock what's outside the component.** A component that calls `fetch` should have `fetch` stubbed the same way pure-logic tests do. A component that uses `next/navigation` should have `useRouter` mocked via `vi.mock("next/navigation", ...)`.

See `ui/AtlasHeader.test.tsx` for the canonical pattern.

## Out of scope (for now)

The following are deliberately not tested yet. They belong in future sessions:

- **3D scene interactions.** The scene engine's Three.js integration would require a canvas mock. Not worth the complexity until a regression in hover/click behavior demonstrates the need.
- **Backend integration.** The atlas tests never hit a real backend. Integration coverage belongs in the backend's own test suite.
- **Route-level end-to-end.** Playwright or similar. Worth revisiting once the core suite is established.

## Canonical commands

```bash
# Run the full suite once
cd atlas && npm test

# Watch mode (reruns on file change)
cd atlas && npm run test:watch

# Verbose reporter — prints every describe/it name.
# This is the canonical "what does the suite cover?" command.
cd atlas && npm test -- --reporter=verbose
```

## When you add a new test file

1. **Create it next to the source file**, not in a central `tests/` folder.
2. **Name it `<source>.test.ts`** or `.test.tsx` for component tests when we add them.
3. **Start with the JSDoc coverage header.** Copy the shape above.
4. **Write `describe`/`it` labels as specifications.** Read them out loud to check.
5. **Run `npm test`** to verify the harness picks it up.
6. **Run `python3 tools/docs-audit/audit.py`** to verify the header passes the audit check.
7. **Include the test file's additions in the same commit** as the source change it covers, or the commit that introduces the unit being tested.

## Where to go next

- [`atlas/docs/the-structure.md`](./the-structure.md) — the layout and architectural principles this testing convention fits inside.
- [`atlas/README.md`](../README.md) — the quick-start running commands.
- [`tools/docs-audit/checks/atlas_test_headers.py`](../../tools/docs-audit/checks/atlas_test_headers.py) — the audit check that enforces the JSDoc header convention.
