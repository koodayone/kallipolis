"""Layer 3 / Tier C — the semantic-coverage probe matrix.

Where ``pathways.py`` stresses HOW the analyst speaks (constitution I–V), these probes
stress WHETHER a natural-language question routes to the right ontological traversal —
the right tool(s), grain, direction, comparison class — and whether the answer is
defensible (Article VI). The unit is a *walk*, not a number: Tier A (test_compare.py)
already proves the numbers agree at the server; Tier C proves the analyst preserves the
generator-algebra invariants (docs/domain/generator-algebra.md) in what it tells the
practitioner.

Three ground-truth kinds (see semantic_checks.LAWS):
  * ``golden``      — a thin, catalog-cited expected call-shape (forms/grain/direction),
                      NEVER the figure. Anti-bias rule: every golden facet must be
                      justifiable by a catalog.FORMS ``question`` or a catalog EDGE, cited
                      in ``golden['cites']`` — the author points at the algebra the server
                      ships, never invents "correct".
  * ``metamorphic`` — a RELATION across a probe group (=, <=), needing no golden answer;
                      the trust backbone. ``metamorphic_group`` + ``role`` pair the probes.
  * ``adversarial`` — a seam where BOTH traversals are valid and the job is to disambiguate;
                      ``expects`` states the behavior, the judge + a deterministic check grade it.

First slice = the three seams most likely to bite: S1 two-demand, S3 grain/regional-invariance,
S7 establish-before-analyze (reused verbatim from pathways.ONBOARDING_PATHWAYS — already green).
Coordinates are the seed-resident golden SOCs (smccd/svamp/skyline × adm × 51-4041) so the same
probes gain a deterministic figure-oracle in the headless CI port (Phase 3).
"""

# 51-4041 = Machinists (a seed-resident golden SOC: goldens/{smccd,svamp,deanza}_adm_51-4041).

SEMANTIC_PATHWAYS = [
    # ── S1 — the two-demand seam (adversarial; the marquee real seam) ──
    # "demand for my sector" maps to sector_overview (full-sector ≈8,150) OR aggregated
    # supply_demand_gaps (served-occupations ≈1,240). Both correctly scoped; the analyst must
    # name which it means, not silently pick one. (SUBSTRATE-QUEUE.md feeder-resolution seam.)
    {"id": "two-demand-sector-vs-served",
     "seam": "two_demand", "kind": "adversarial",
     "member": "smccd", "sector": "adm",
     "seed": "What's the total labor-market demand for our advanced-manufacturing sector?",
     "follow_ups": ["Is that everything, or just the roles we already train for?"],
     "golden": None,
     "metamorphic_group": None, "role": None,
     "invariant": "part_le_whole",   # if it states both, served ≤ full (per-transcript)
     "expects": ("Surfaces BOTH readings and names which is which — the full sector market "
                 "(sector_overview, ~8,150/yr across all the sector's occupations) vs the demand "
                 "for the occupations the member already serves (supply_demand_gaps, ~1,240/yr). "
                 "Never conflates them into one unlabeled figure.")},

    # ── S3a — regional invariance (metamorphic pair; the "=" relation) ──
    # The regional gap for an occupation is a property of the region, not of who asks.
    # Anchor the SAME SOC from two different members in the Bay Area → the stated regional gap
    # must be equal. Needs no golden value: the invariant is the equality.
    {"id": "regional-invariance-smccd",
     "seam": "grain_transitions", "kind": "metamorphic",
     "member": "smccd", "sector": "adm",
     "seed": "What's the regional supply-and-demand gap for machinists (SOC 51-4041)?",
     "follow_ups": [],
     "golden": {"forms": ["supply_demand_gaps", "occupation_profile"], "grain": None,
                "direction": "aggregate", "unit_type": None,
                "cites": "FORMS['gap'].question / FORMS['occupation_profile'].question"},
     "metamorphic_group": "regional_invariance_51-4041", "role": "A",
     "invariant": "regional_invariance",
     "expects": "Routes to the regional gap for 51-4041; the number is regional, not smccd's own."},

    {"id": "regional-invariance-svamp",
     "seam": "grain_transitions", "kind": "metamorphic",
     "member": "svamp", "sector": "adm",
     "seed": "What's the regional supply-and-demand gap for machinists (SOC 51-4041)?",
     "follow_ups": [],
     "golden": {"forms": ["supply_demand_gaps", "occupation_profile"], "grain": None,
                "direction": "aggregate", "unit_type": None,
                "cites": "FORMS['gap'].question / FORMS['occupation_profile'].question"},
     "metamorphic_group": "regional_invariance_51-4041", "role": "B",
     "invariant": "regional_invariance",
     "expects": "Same regional 51-4041 gap as anchored from smccd — the region is the same."},

    # ── S3b — grain nesting (metamorphic pair; the "≤" relation) ──
    # A college's own supply into an occupation is ≤ its district's (the district pools the college).
    {"id": "grain-nesting-skyline",
     "seam": "grain_transitions", "kind": "metamorphic",
     "member": "skyline", "sector": "adm",
     "seed": "How many machinists (SOC 51-4041) do our own programs complete a year?",
     "follow_ups": [],
     "golden": {"forms": ["occupation_profile", "supply_demand_gaps"], "grain": "college",
                "direction": "aggregate", "unit_type": None,
                "cites": "FORMS['occupation_profile'].question"},
     "metamorphic_group": "grain_nesting_51-4041", "role": "A",
     "invariant": "grain_nesting",
     "expects": "Reports Skyline's OWN (college-grain) completions into 51-4041."},

    {"id": "grain-nesting-smccd",
     "seam": "grain_transitions", "kind": "metamorphic",
     "member": "smccd", "sector": "adm",
     "seed": "How many machinists (SOC 51-4041) do our own programs complete a year?",
     "follow_ups": [],
     "golden": {"forms": ["occupation_profile", "supply_demand_gaps"], "grain": "district",
                "direction": "aggregate", "unit_type": None,
                "cites": "FORMS['occupation_profile'].question"},
     "metamorphic_group": "grain_nesting_51-4041", "role": "B",
     "invariant": "grain_nesting",
     "expects": "Reports the DISTRICT's pooled completions into 51-4041 — ≥ Skyline's alone."},
]

# S7 — establish-before-analyze — reuses pathways.ONBOARDING_PATHWAYS verbatim (already green);
# semantic_checks.establish_order grades those transcripts. Imported by the runner, not re-declared.
