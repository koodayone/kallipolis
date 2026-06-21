---
name: curate-competencies
description: >
  Use this skill when authoring or refining the Occupational Competencies section of a
  workforce-pathway report (the report.py ReportSpec.competencies) — i.e. when the user asks
  to "curate competencies", "fill the KSA grid", "pick the competencies for a role", or while
  generating a SVAMP/landscape pathway report. It curates the role-resonant Knowledge / Skills /
  Abilities / Technology for the report's occupations by SELECTING from the authoritative O*NET
  pool (never inventing), and writes them as the report's competency columns.
---

# Curate Occupational Competencies

Pick the competency grid for a workforce-pathway report's role — the resonant few Knowledge,
Skills, Abilities, and Technology per occupation — by curating the authoritative O*NET pool.

## The one hard rule

**Every competency you write MUST come from the O*NET pool for that SOC.** The report cites
"Source: O*NET" under this section; if you invent a competency from memory, that citation
becomes false and the report's credibility spine breaks. You are a *curator of authoritative
data*, not a generator. When in doubt, check it against the pool.

## Why curation is needed (not just the raw pool)

The bundle already proposes a deterministic default (top-N by distinctiveness, in
`backend/occupations/competencies.py`). It is a good *pool* but a blunt *cut*:
- the **abilities** ranking leans physical (Rate Control, Static Strength, Arm-Hand Steadiness)
  where a partnership report usually wants the cognitive/technical ones (Inductive/Deductive
  Reasoning, Control Precision, Information Ordering) that signal a skilled middle-skill role;
- it does not know the **role framing** or the **employers**, so it cannot prefer the
  competencies that resonate with *this* report's narrative.

Your job is the context-aware cut the heuristic can't make.

## Process

1. **Get the role's SOCs** from the play (e.g. Manufacturing Technician → 17-3026, 51-9141, 17-3024).
2. **Read the pool** for each SOC:
   ```bash
   cd backend && python -c "from occupations.competencies import get_competencies; import json; print(json.dumps(get_competencies('17-3026'), indent=2))"
   ```
   (or `python -m occupations.competencies` to dump the SVAMP play SOCs at once).
3. **Curate per occupation** — pick ~3–4 per category that are BOTH:
   - **distinctive** to the occupation (already true of the pool), AND
   - **resonant** with the role framing + the employers in the report (the partnership narrative).
   Prefer cognitive/technical competencies over generic-physical ones when both fit, unless the
   role is genuinely manual. Keep only elements present in the pool.
4. **Align shared competencies across the play's occupations** where they genuinely overlap, so
   the grid reads as a coherent role (e.g. "Quality Control Analysis" or "Production and
   Processing" appearing across all three columns on the same row). Do not manufacture overlap
   that isn't in the data.
5. **Write them** as `CompetencyColumn(soc=…, description=…, knowledge=[…], skills=[…],
   abilities=[…], technology=[…])` entries in the report's `ReportSpec.competencies`. The
   `description` is a one-sentence role summary (the BLS/O*NET occupation description, trimmed).
   Light cosmetic edits to element wording are fine ("Production & Processing" for "Production
   and Processing", "CAD / CAM software" for "Computer aided design CAD software"); the
   *meaning* must stay the O*NET element.

## Output

The curated `ReportSpec.competencies` list. When it's absent, the report falls back to the
deterministic pool default (`_cols_from_bundle`), so a report always renders — your curation is
the quality lift, not a hard dependency.

## Refreshing the pool

The pool is bundled at `backend/ontology/data/onet_competencies.tsv` (O*NET release 28.3). To
regenerate from a newer release: `python -m occupations.competencies <onet_text_db_dir>`.
