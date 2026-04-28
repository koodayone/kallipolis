# Preview mode assets

This directory holds the assets that make the atlas's preview mode legible to
prospective pilot partners: curated partnership proposals and the
preview-feedback endpoint helper.

## Files

- `mode.ts` — `PREVIEW_MODE` flag derived from `NEXT_PUBLIC_AUTH_ENABLED`.
  Defaults to auth-on; set `NEXT_PUBLIC_AUTH_ENABLED=false` to enable preview.
- `seededPartnerships.ts` — `SEEDED_PARTNERSHIPS: Record<collegeId, SavedProposal[]>`
  with one partnership per featured college. The artifact carries four
  narrative sections (executive summary, occupational demand, curriculum
  alignment, student impact) plus a tabular Strong Workforce evidence block.
- `reportFlag.ts` — POSTs structured feedback to `NEXT_PUBLIC_FLAG_ENDPOINT`
  (Formspree in production).

## Seeded ID convention

Stable, human-readable slugs — never random UUIDs. This keeps git diffs
meaningful across regenerations.

```
seed-<collegeId>-<nn>
```

Examples: `seed-shasta-01`, `seed-foothill-01`, `seed-compton-01`.

## Regeneration procedure

When the proposal schema (`PROPOSAL_SCHEMA_VERSION` in `savedProposals.ts`)
bumps, or when data authorities change enough that seeded narratives look
stale, regenerate:

1. Check out `main` (auth still enabled) and run the atlas + backend
   locally. Log in to each of the featured colleges in `FEATURED_COLLEGES`.
2. For each college, open Partnerships → Build Mode and generate one
   proposal. Iterate with Reject & Revise until the narrative is
   presentation-grade. Save it.
3. In DevTools for each college page:
   ```js
   copy(JSON.parse(
     localStorage.getItem(`kallipolis-saved-proposals-${collegeId}`),
   ));
   ```
4. Paste into a scratch file. Replace each partnership's random `id` with
   the stable slug convention. Normalize `savedAt` to an ISO date (not
   timestamp) for stable diffs.
5. Populate `seededPartnerships.ts` with typed entries. Run `npm test` —
   the schema-version guard in `seededContent.test.ts` fails the build if
   drift is introduced.
6. Commit.

## Why these exist

In preview mode, users cannot save (`Save` is disabled with a pilot-contact
tooltip), so without seeded partnerships the Manage Mode tab would always be
empty. These seeds are the demonstration substrate that makes the partnership
flow legible to a visiting prospect without gating access.
