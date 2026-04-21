# Department mapping schema

This directory holds the `{prefix → canonical_name}` mapping that powers
Stage 2.5 of the course extraction pipeline. At load time a college's
mapping is `{**base, **overlay[college]}` — overlay wins on conflict.

## Files

- `base.json` — universal prefixes with stable names across CA CCCs (e.g.
  `MATH → Mathematics`). Keep lean. If any college is likely to use a
  different display name, put the entry in the overlay instead.
- `overlays/{college}.json` — per-college additions and overrides.
  College-specific programs (e.g. Foothill's `APSM → Apprenticeship: Sheet
  Metal`) live here.

## File format

```json
{
  "_meta": {
    "description": "...",
    "last_reviewed": "YYYY-MM-DD",
    "seeded_from": "free-text explanation of how this file was populated",
    "allowed_collisions": [["POLI", "POLS"]]
  },
  "prefixes": {
    "PREFIX": "Human-Readable Name",
    ...
  }
}
```

- `_meta.allowed_collisions` — list of prefix groups that are deliberately
  allowed to share a canonical name. Example: `POLI` and `POLS` both map
  to "Political Science" because they're the old and new CCCN numbering
  for the same subject.

## Invariants (enforced at load time by the resolver)

1. Every value is a non-empty string.
2. No value equals its key (bare codes like `"STAT"` as a display label are
   a UI failure).
3. No value is shorter than 3 characters.
4. No value ends with a parenthesized all-caps code like `"Dance (DANC)"`
   — those are extraction artifacts, strip them.
5. Distinct prefixes must not collide on the same name unless whitelisted
   in `_meta.allowed_collisions`.

## Adding a new college

```
python scripts/seed_department_mapping.py --college {key}
```

The seeder scans the catalog PDF for `Subject Name (PREFIX)` section
headers, compares against prefixes present in `{key}_enriched.json`, and
writes `overlays/{key}.proposed.json` plus a report of any unmapped
prefixes the operator must fill in manually. Review, rename to
`overlays/{key}.json`, commit.

## Multi-word prefixes

Course codes like `C S 81`, `D A 50`, `V T 51A`, `R T 53AL` have
multi-word prefixes with significant internal spaces. The resolver's
`extract_prefix` handles them by splitting at the final whitespace and
validating the last token looks like a course number (`[A-Z]?\d+[A-Z]*`).
Use the full multi-word prefix as the key in the overlay JSON:

```json
"C S": "Computer Science",
"V T": "Veterinary Technology"
```
