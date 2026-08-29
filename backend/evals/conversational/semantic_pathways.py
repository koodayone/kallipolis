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

Phase-1 first slice = the three seams most likely to bite: S1 two-demand, S3 grain/regional-invariance,
S7 establish-before-analyze (reused verbatim from pathways.ONBOARDING_PATHWAYS — already green).
Phase 2 widens the covering set toward the plan's ~20-probe target: S-coord coordinate-identity
(tool-independence, the two-window spec), S2 forward/reverse (crosswalk membership), S4 comparison-class,
S5 absence-vs-zero, S6 non-summable pools, and a form top-up (unmet_demand, regional_employers,
member_portfolio) so every analytical form routes at least once. Coordinates are the seed-resident
golden SOCs (smccd/svamp/deanza/skyline × adm × 51-4041, fed by TOP 095630) so the same probes gain a
deterministic figure-oracle in the headless CI port (Phase 3).
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

    # ══ Phase 2 ══════════════════════════════════════════════════════════════════════════════

    # ── S-coord — coordinate identity (metamorphic pair; the "=" relation, TOOL-independent) ──
    # A measure at a coordinate is one value however REACHED. Machinists' regional openings (~510) is
    # the same via occupation_profile(51-4041) and via a compare(unit_type=occupation, regional_openings)
    # row for 51-4041 — two questions that route to DIFFERENT tools but land on the SAME coordinate.
    # Differs from regional_invariance (which fixes the coordinate and varies WHO asks → grain routing):
    # here the coordinate is fixed and WHICH TOOL answers varies → tool routing. The check is
    # coordinate-AWARE (matches SOC before asserting equality) so it does NOT collide with the
    # two-demand seam, where sector_overview (~8,150) and supply_demand_gaps (~1,240) are the SAME
    # tool-independent question but DIFFERENT coordinates (full-sector vs served). This law is the
    # spec for the dashboard⇄MCP unification — the two-window invariant, the dashboard as the 2nd path.
    {"id": "coordinate-identity-occprofile",
     "seam": "coordinate_identity", "kind": "metamorphic",
     "member": "deanza", "sector": "adm",
     "seed": "What's the regional demand — the annual openings — for machinists (SOC 51-4041)?",
     "follow_ups": [],
     "golden": {"forms": ["occupation_profile"], "grain": None, "direction": "aggregate",
                "unit_type": None, "cites": "FORMS['occupation_profile'].question"},
     "metamorphic_group": "coordinate_identity_openings_51-4041", "role": "A",
     "invariant": "coordinate_identity",
     "expects": "Routes to the occupation's regional picture; reports annual openings for 51-4041 (~510)."},

    {"id": "coordinate-identity-compare",
     "seam": "coordinate_identity", "kind": "metamorphic",
     "member": "deanza", "sector": "adm",
     "seed": ("Rank our advanced-manufacturing sector's occupations by regional openings — where do "
              "machinists (51-4041) land, and how many openings do they have?"),
     "follow_ups": [],
     "golden": {"forms": ["compare"], "grain": None, "direction": "aggregate",
                "unit_type": "occupation", "cites": "compare REGISTRY['occupation']['regional_openings']"},
     "metamorphic_group": "coordinate_identity_openings_51-4041", "role": "B",
     "invariant": "coordinate_identity",
     "expects": ("Ranks the sector's occupations by regional openings; the 51-4041 row reads the SAME "
                 "openings (~510) as occupation_profile — the figure is tool-independent.")},

    # ── S2 — forward/reverse consistency (per-transcript; the "⊇" relation, NEVER magnitude) ──
    # One conversation walks the crosswalk both ways: forward from a program to the occupations it
    # prepares for, then reverse from an occupation to the programs feeding it. If the analyst says the
    # Machining program (095630) prepares for machinists (51-4041), then machinists' feeder set must
    # contain 095630. Membership only — the TOP→CIP→SOC crosswalk is many-to-many and lossy, so the
    # magnitudes are NOT comparable; the analyst must flag that looseness (SAL_LOSSY_CROSSWALK).
    {"id": "forward-reverse-machining",
     "seam": "forward_reverse", "kind": "golden",
     "member": "deanza", "sector": "adm",
     "seed": "What occupations does our Machine Tool Technology program (TOP 095630) prepare students for?",
     "follow_ups": ["And which of our programs feed machinists (SOC 51-4041)?"],
     "golden": {"forms": ["program_pathways"], "grain": None, "direction": "forward",
                "unit_type": None, "cites": "FORMS['pathway'].question / EDGES['gap']→pathway"},
     "metamorphic_group": None, "role": None,
     "invariant": "forward_reverse",
     "expects": ("Forward: names the occupations 095630 prepares for (incl. 51-4041). Reverse: the "
                 "programs feeding 51-4041 include 095630 — the edge is bidirectionally present. Flags "
                 "the many-to-many looseness (a graduate is qualified across these, not assigned to one).")},

    # ── S5 — absence vs zero (per-transcript; a gated/blank field is unknown, never 0) ──
    # SMCCD runs no program feeding 51-4041, so its own completions are a STRUCTURAL zero — a verifiable
    # no-program fact, named as such, distinct from an unknown/gated value read as 0. The regional gap
    # (510) is still reported. (PR #120: a member's un-served occupation routes to occupation_profile.)
    {"id": "absence-structural-zero",
     "seam": "absence_zero", "kind": "adversarial",
     "member": "smccd", "sector": "adm",
     "seed": "How many machinists (SOC 51-4041) do our own programs complete a year, and what's the gap?",
     "follow_ups": ["So our supply is just zero?"],
     "golden": {"forms": ["occupation_profile", "supply_demand_gaps"], "grain": "district",
                "direction": "aggregate", "unit_type": None,
                "cites": "FORMS['occupation_profile'].question"},
     "metamorphic_group": None, "role": None,
     "invariant": "absence_not_zero",
     "expects": ("SMCCD's own completions into 51-4041 are a STRUCTURAL zero — named 'no program feeding "
                 "it', a verifiable fact, NOT an unknown read as 0. The regional gap (510) is still given; "
                 "a gated/blank field would be called unknown, never 0.")},

    # ── S4 — comparison class (classification; route to the right unit_type, name the axis) ──
    # "How do we compare?" routes to the right comparison CLASS: a cross-institution question compares
    # COLLEGES (positioning), not programs; a "which is best?" bait must resolve to a named axis, never a
    # blended score. No metamorphic law — graded by golden_traversal (right unit_type) + the judge.
    {"id": "comparison-class-colleges",
     "seam": "comparison_class", "kind": "adversarial",
     "member": "smccd", "sector": "adm",
     "seed": "How do we stack up against the other colleges in the region for advanced manufacturing?",
     "follow_ups": ["Who leads, and on what?"],
     "golden": {"forms": ["compare"], "grain": None, "direction": "aggregate",
                "unit_type": "college", "cites": "compare REGISTRY['college']"},
     "metamorphic_group": None, "role": None,
     "invariant": None,
     "expects": ("Routes to a COLLEGE comparison (compare unit_type=college), not a program comparison — "
                 "positioning within the region, named by axis (supply share / supply), never a "
                 "competitive score.")},

    {"id": "comparison-class-best-bait",
     "seam": "comparison_class", "kind": "adversarial",
     "member": "smccd", "sector": "adm",
     "seed": "Which single program of ours is the best?",
     "follow_ups": ["Just pick one for me."],
     "golden": {"forms": ["compare"], "grain": None, "direction": "aggregate",
                "unit_type": "program", "cites": "compare REGISTRY['program']"},
     "metamorphic_group": None, "role": None,
     "invariant": None,
     "expects": ("Treats 'best' as a choice among named axes (completions, addressable demand, wage, "
                 "supply share) — ranks by the most fitting, NAMES it, offers the others; a forced pick "
                 "is CONTINGENT on the axis, never one blended score.")},

    # ── S6 — non-summable addressable pools (reuses part_le_whole; the pools overlap, never sum) ──
    # A program's addressable demand is a sum-across pool it COMPETES for, shared with other programs —
    # summing addressable demand across programs double-counts the same openings. The analyst must
    # refuse the sum and give the distinct sector total instead. Graded by golden_traversal + the judge.
    {"id": "non-summable-addressable",
     "seam": "non_summable", "kind": "adversarial",
     "member": "smccd", "sector": "adm",
     "seed": ("Add up the addressable demand across all our advanced-manufacturing programs — what's the "
              "total market we're addressing?"),
     "follow_ups": ["So that sum is our real total addressable market?"],
     "golden": {"forms": ["sector_overview", "compare"], "grain": None, "direction": "aggregate",
                "unit_type": None, "cites": "FORMS['sector_overview'].guardrail (addressable pools overlap)"},
     "metamorphic_group": None, "role": None,
     "invariant": "part_le_whole",
     "expects": ("Refuses to sum addressable-demand pools — they OVERLAP (programs share the same "
                 "openings), so the sum double-counts. Gives the distinct sector total, names the overlap.")},

    # ── Form top-up — the analytical forms not otherwise exercised route correctly (classification) ──
    {"id": "form-unmet-demand",
     "seam": "form_topup", "kind": "golden",
     "member": "smccd", "sector": "adm",
     "seed": "What in-demand occupations is our region hiring for that we train no one into?",
     "follow_ups": [],
     "golden": {"forms": ["unmet_demand"], "grain": None, "direction": "aggregate",
                "unit_type": None, "cites": "FORMS['unmet_demand'].question"},
     "metamorphic_group": None, "role": None,
     "invariant": None,
     "expects": "Routes to greenfield/unmet demand (occupations served by no one), not the served-gap view."},

    {"id": "form-regional-employers",
     "seam": "form_topup", "kind": "golden",
     "member": "smccd", "sector": "adm",
     "seed": "Which regional employers hire machinists (SOC 51-4041) — who could we convene?",
     "follow_ups": [],
     "golden": {"forms": ["regional_employers"], "grain": None, "direction": "aggregate",
                "unit_type": None, "cites": "FORMS['regional_employers'].question"},
     "metamorphic_group": None, "role": None,
     "invariant": None,
     "expects": "Routes to regional employers for 51-4041 (candidate partners to convene, not a hiring roster)."},

    {"id": "form-member-portfolio",
     "seam": "form_topup", "kind": "golden",
     "member": "smccd", "sector": None,
     "seed": "Give me the overall picture of where we stand across all our sectors.",
     "follow_ups": [],
     "golden": {"forms": ["member_portfolio"], "grain": "district", "direction": "aggregate",
                "unit_type": None, "cites": "FORMS['member_portfolio'].question"},
     "metamorphic_group": None, "role": None,
     "invariant": None,
     "expects": "Routes to the whole-institution portfolio in ONE call (member_portfolio), not a sector loop."},
]

# S7 — establish-before-analyze — reuses pathways.ONBOARDING_PATHWAYS verbatim (already green);
# semantic_checks.establish_order grades those transcripts. Imported by the runner, not re-declared.
