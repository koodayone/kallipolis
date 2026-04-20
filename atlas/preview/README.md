# Preview mode assets

This directory holds the assets that make the atlas's preview mode legible to
prospective pilot partners: curated partnership proposals, curated SWP
project artifacts, and the preview-feedback endpoint helper.

## Files

- `mode.ts` — `PREVIEW_MODE` flag derived from `NEXT_PUBLIC_AUTH_ENABLED`.
  Defaults to auth-on; set `NEXT_PUBLIC_AUTH_ENABLED=false` to enable preview.
- `seededPartnerships.ts` — `SEEDED_PARTNERSHIPS: Record<collegeId, SavedProposal[]>`
  with three partnerships per college (advisory board, internship,
  curriculum co-design).
- `seededSwpProjects.ts` — `SEEDED_SWP_PROJECTS: Record<collegeId, SavedSwpProject[]>`
  with 1–2 SWP artifacts per college. Each entry's `partnershipId` must match
  the id of a seeded partnership.
- `reportFlag.ts` — POSTs structured feedback to `NEXT_PUBLIC_FLAG_ENDPOINT`
  (Formspree in production).

## Seeded ID convention

Stable, human-readable slugs — never random UUIDs. This keeps the SWP →
partnership reference stable across seed regenerations and makes git diffs
meaningful.

```
seed-<collegeId>-<engagementType>-<nn>
```

Examples: `seed-shasta-advisory-01`, `seed-foothill-internship-02`,
`seed-compton-curriculum-01`.

## Regeneration procedure

When the proposal schema (`PROPOSAL_SCHEMA_VERSION` in `savedProposals.ts`)
bumps, or when data authorities change enough that seeded narratives look
stale, regenerate:

1. Check out `main` (auth still enabled) and run the atlas + backend
   locally. Log in to each of the 8 colleges in `FEATURED_COLLEGES`.
2. For each college, open Partnerships → Build Mode and generate one
   proposal per engagement type. Iterate with Reject & Revise until the
   narrative is presentation-grade. Save each.
3. Open Strong Workforce → Build Mode. For 1–2 saved partnerships, draft
   and save an SWP project.
4. In DevTools for each college page:
   ```js
   copy({
     partnerships: JSON.parse(
       localStorage.getItem(`kallipolis-saved-proposals-${collegeId}`),
     ),
     swp: JSON.parse(
       localStorage.getItem(`kallipolis-saved-swp-${collegeId}`),
     ),
   });
   ```
5. Paste into a scratch file. Replace each partnership's random `id` with
   the stable slug convention. Update every SWP's `partnershipId` to match
   the new slugs. Normalize `savedAt` to an ISO date (not timestamp) for
   stable diffs.
6. Populate `seededPartnerships.ts` and `seededSwpProjects.ts` with typed
   entries. Run `npm test` — the schema-version guard in
   `seededContent.test.ts` fails the build if drift is introduced.
7. Commit. Land Phase 0 deletions (auth removal) on a separate PR only
   after seeds are in place; the auth-live flow is what makes seed
   curation possible.

## Why these exist

The SWP flow's `buildSwpRequest()` consumes a `SavedProposal` — there is no
SWP without a saved partnership upstream. In preview mode, users cannot
save (`Save` is disabled with a pilot-contact tooltip), so without seeded
partnerships the SWP surface would be empty. These seeds are the
demonstration substrate that makes the full partnership lifecycle
(discover → justify) legible without gating access.
