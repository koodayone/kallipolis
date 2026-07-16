"""The Tier 1 catalog — a graph, not a set (§1.3).

Four analytical forms, each a designed template instantiated at a coordinate.
This module holds their static identity (the practitioner question, the domain
*meaning*, the load-bearing guardrail), the adjacency EDGES (the ideal
practitioner's "what to ask next", §5.2 — the same object that will later power
Tier 2 → Tier 1 routing), and the salience vocabulary (§5.3: computed epistemic
flags, never a reading of the numbers).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mcp_server.envelope import NextMove
from mcp_server.scope import coordinate_of


# ── The four forms (static identity) ──────────────────────────────────────

@dataclass(frozen=True)
class Form:
    id: str
    question: str      # the practitioner question — seeds the tool description
    meaning: str       # static domain meaning (§5.3) → framing.meaning
    guardrail: str     # the §1.2 load-bearing guardrail → licensing


FORMS: dict[str, Form] = {
    "gap": Form(
        id="gap",
        question="Where does regional demand outrun what the region's colleges produce?",
        meaning=(
            "A supply–demand gap is regional annual openings minus the whole region's "
            "projected completions, per occupation — regional demand against regional "
            "supply. The institution's own completions are its share of that regional "
            "supply. Positive means the region hires more than its colleges are projected "
            "to complete."),
        guardrail=(
            "'Supply' is projected completions — COE's Annual Projected Supply method (a "
            "trailing 3-year average of DataMart completions), reconstructed on current "
            "DataMart data; it is the gap denominator, read as a projection rather than one "
            "year's raw count (see latest_year_supply). The gap is REGIONAL; the institution's "
            "own supply is a separate figure (its share), never the gap itself. A member's "
            "latest-year change moves its own share, not the regional gap — do not read a "
            "regional trend from one institution's single year."),
    ),
    "coverage": Form(
        id="coverage",
        question="Which colleges have a program feeding each in-demand occupation?",
        meaning=(
            "Coverage classifies each (college, occupation) as Covered / Partial / Gap "
            "by whether a feeding program both enrolls and awards. It is the "
            "institutional legibility of the gap across the member's colleges."),
        guardrail=(
            "The Covered/Partial/Gap thresholds are an explicit classification "
            "(enrolled AND awarded = covered; exactly one = partial; neither = gap), "
            "not an implied score."),
    ),
    "pathway": Form(
        id="pathway",
        question="What does a program prepare students for, or what feeds an occupation?",
        meaning=(
            "A pathway is the institutional TOP→CIP→SOC crosswalk between a program and "
            "the occupations it prepares students for (or the reverse). The bridge is an "
            "external, authoritative mapping, not an internal skills index."),
        guardrail=(
            "The TOP→CIP→SOC crosswalk is many-to-many; the fan-out is surfaced, never "
            "collapsed into a single per-program number (which would double-count)."),
    ),
    "occupation_profile": Form(
        id="occupation_profile",
        question="What is the whole picture for this occupation — demand, who trains for it, who hires?",
        meaning=(
            "An occupation profile is the regional picture of one occupation: its "
            "demand (openings, median wage, employment, projected growth), the "
            "programs across the region that feed it, the total regional projected "
            "supply and the gap, the top regional employers, and the sector it "
            "belongs to. The region is derived from the institution; the occupation, "
            "not a sector, is the entry point."),
        guardrail=(
            "Demand is the regional occupational signal, not graduates' earnings. "
            "Supply is projected completions across the region — COE's Annual Projected "
            "Supply method (a 3-year average of DataMart completions), reconstructed on "
            "current DataMart data; read it as a projection, not one year's raw count. "
            "The program→occupation crosswalk is many-to-many, so a feeding program 'can "
            "lead to' the occupation, it is not exclusive to it."),
    ),
    "regional_employers": Form(
        id="regional_employers",
        question="Which regional employers hire for this occupation — who could the member convene?",
        meaning=(
            "Ranks regional employers by how prominently each employer's industry staffs the "
            "target occupations (BLS OES staffing share). It surfaces candidate partners the "
            "member could convene — not a hiring roster."),
        guardrail=(
            "Ranked by OES industry staffing share; OES-suppressed cells are dropped (not "
            "marked), and the shortlist ('shown') is not the whole candidate pool ('total')."),
    ),
    "unmet_demand": Form(
        id="unmet_demand",
        question="Which in-demand occupations does the region hire for that this member graduates no one into?",
        meaning=(
            "Greenfield demand is the set of occupations the member's region demands but the "
            "member itself supplies zero completers for — regional demand with no local "
            "pipeline. It is filtered to community-college-servable education levels, a "
            "living-wage floor, and a meaningful-openings floor, then ranked by opportunity "
            "(annual openings × median wage). It is the complement of the member-anchored gap "
            "view: that view is scoped to occupations the member already serves; this one "
            "surfaces exactly the ones it does not."),
        guardrail=(
            "Zero member supply is a verifiable graph fact (no completer feeds the occupation), "
            "not a judgment that the member SHOULD launch it. Demand is COE PROJECTED openings; "
            "the quality thresholds (servable education, wage ≥ $50k, ≥ 100 openings/yr) are "
            "explicit filters, not a score, and feasibility, cost, and mission fit are out of scope."),
    ),
    "member_portfolio": Form(
        id="member_portfolio",
        question="How is this whole institution doing across every sector it runs, against regional demand?",
        meaning=(
            "The member-anchor orientation — the top of the descent. One row per sector the member "
            "runs: total regional demand across that sector's occupations vs the region's total "
            "projected completions feeding them, the member's own supply and its share, and the gap "
            "— plus an institution-wide total across all its sectors. It answers a whole-institution "
            "portfolio question in ONE call; the per-sector (sector_overview) and per-occupation "
            "(gap) views are drills the practitioner walks turn by turn, not steps taken here."),
        guardrail=(
            "All figures are plain sums; the institution-wide totals are over the DEDUPED union of "
            "the member's sectors' occupations (an occupation in two sectors counted once), so they "
            "are defensible as summed. Supply is a 3-year DataMart projection; the gap is REGIONAL; "
            "the member's supply is its share of the region's."),
    ),
    "sector_overview": Form(
        id="sector_overview",
        question="How does this member's whole sector portfolio stack up against regional demand?",
        meaning=(
            "The sector-anchor orientation — the home base for a portfolio question, PROGRAM-FORWARD. "
            "The summary is the sector aggregate (total regional demand vs the region's projected "
            "completions, the member's supply and its share); the rows are the member's PROGRAMS in "
            "the sector, each with its completions and its addressable demand (the openings across the "
            "occupations it feeds), ranked by that market. It answers 'how is my [sector] doing, and "
            "which program should I look at' — drill a program for its occupations, or the gap tool "
            "for the occupation-level view."),
        guardrail=(
            "The aggregate figures are plain sums across the sector's DISTINCT occupations and feeder "
            "programs, each counted once (defensible as COE's own method). A program's addressable "
            "demand is a sum-across pool it COMPETES for — shared with other programs, not exclusive, "
            "and not summable across programs. Supply is a 3-year DataMart projection; the gap is "
            "REGIONAL; the member's supply is its share of the region's."),
    ),
    "compare": Form(
        id="compare",
        question="How do this member's analogous units — its programs, the sector's occupations, or the region's colleges — rank against each other on a chosen measure?",
        meaning=(
            "Comparison ranks a set of analogous units — a member's programs, the sector's occupations, "
            "or the region's colleges — by a chosen criterion, showing every unit's full profile sorted "
            "by that named axis. It is what turns a measure into a decision: which program is biggest or "
            "fastest-growing, which occupation is most in-demand or highest-paying, which college leads "
            "on supply. The axes admissible for each unit type are the criteria menu; rank by one and "
            "name it — never by a blended 'score'."),
        guardrail=(
            "Every criterion is a plain count that adds up (openings, completions, employment), a ratio "
            "measured AT the unit's own grain (supply share, the trends), or a directly-measured outcome "
            "(the graduate-wage figures) — never a weighted composite. An occupation's median wage and "
            "growth are native to the occupation (its regional OES signal); a PROGRAM 'wage' blended from "
            "its occupations' wages, or a growth rate carried down to a program, WOULD be a composite and "
            "is not a criterion. A program's graduate wage is the measured, statewide-pooled cohort (its "
            "largest recipient type), not this member's own graduates, and medians are never summed. "
            "'addressable_gap' is a program's addressable demand minus the REGIONAL supply into the "
            "occupations it feeds — NOT the sector/occupation gap supply_demand_gaps reports. Trends "
            "compare same-season terms to avoid a seasonal artifact; college figures are per single "
            "college — positioning within the region, never a competitive ranking."),
    ),
}


# ── Form-id → public tool name ────────────────────────────────────────────
# A next-move is a CALL TARGET: the model routes to it, so its `form` must be a
# name it can actually invoke. Post-retirement the surface is the five VERBS (+ the
# list helper): an internal form-id ("gap", "coverage", …) is reached by a verb whose
# coordinate carries the entity/lens it dispatches on. This map names that verb; the
# entity/lens are set by `as_move`. server.py registers each verb under the same name
# (a coherence test pins TOOL_NAME.values() ⊆ the registered tools). Includes the two
# Tier-0 ids the gate routes back to.
TOOL_NAME: dict[str, str] = {
    "list_scopes": "list_institutions",
    "orient": "orient",
    "member_portfolio": "orient",
    "sector_overview": "navigate",
    "compare": "compare",
    "gap": "navigate",
    "coverage": "navigate",
    "pathway": "crosswalk",
    "regional_employers": "navigate",
    "occupation_profile": "navigate",
    "unmet_demand": "navigate",
}

# The lens a verb sets to reach a form-id's view (blank ⇒ dispatched by sector/entity alone).
_LENS: dict[str, str] = {
    "gap": "gaps",
    "coverage": "coverage",
    "regional_employers": "employers",
    "unmet_demand": "greenfield",
}
# form-ids whose carried SOC rides the coordinate as the verb's entity (the occupation in focus).
_SOC_ENTITY_FORMS = frozenset({"gap", "regional_employers", "occupation_profile"})


def tool_name(form_id: str) -> str:
    """The registered VERB (or the list helper) that reaches a form-id's view — fail-fast on an
    unmapped id so a new form/edge can't silently emit a non-callable next-move."""
    return TOOL_NAME[form_id]


def as_move(form_id: str, coord: "Coordinate", rationale: str = "") -> NextMove:
    """Route a next-move onto the verb surface: `form` = the verb that reaches the form-id's view,
    and a COPY of the coordinate carries the entity/lens the verb dispatches on. The soc/top6 already
    on the coordinate become the entity; occupation_profile is sector-agnostic, so its move drops the
    sector — navigate(entity=<soc>) with no sector resolves to the occupation view."""
    c = coord.model_copy()
    c.lens = _LENS.get(form_id, "")
    if form_id == "pathway":
        c.entity = c.top6 or c.soc or ""          # crosswalk dispatches a program (TOP6) or an occupation (SOC)
    elif form_id in _SOC_ENTITY_FORMS:
        c.entity = c.soc or ""
    if form_id == "occupation_profile" and c.entity:
        c.sector, c.sector_label = "", ""         # sector-agnostic → navigate(entity) hits the occupation view
    return NextMove(form=tool_name(form_id), coordinate=c, rationale=rationale)


# ── The adjacency graph (§5.2: next-moves = catalog edges) ────────────────

@dataclass(frozen=True)
class Edge:
    target: str                 # the target form
    carries: tuple[str, ...]    # coordinate keys to carry forward (e.g. ("soc",))
    rationale: str


EDGES: dict[str, list[Edge]] = {
    "sector_overview": [
        Edge("gap", (), "Drill into the per-occupation supply–demand gaps the member already serves."),
        Edge("unmet_demand", (), "Surface the sector's high-opportunity occupations the member serves no one into."),
        Edge("coverage", (), "See which of the member's colleges cover which programs in the sector."),
    ],
    "coverage": [
        Edge("gap", (), "Size the shortfall behind the coverage picture."),
        Edge("pathway", ("top6",), "Trace the selected program to the occupations it prepares for."),
    ],
    "gap": [
        Edge("regional_employers", ("soc",), "Identify regional employers to convene around the gapped occupation."),
        Edge("pathway", ("soc",), "See which programs feed the gapped occupation."),
    ],
    "pathway": [
        Edge("coverage", (), "Return to who covers this sector across the member's colleges."),
        Edge("regional_employers", ("soc",), "Find regional employers hiring for this occupation."),
    ],
    "regional_employers": [
        Edge("gap", (), "Quantify the supply–demand gap these employers face."),
        Edge("coverage", (), "See which colleges cover the occupations these employers hire."),
    ],
    "unmet_demand": [
        Edge("occupation_profile", ("soc",),
             "Drill into a surfaced greenfield occupation — its full demand, who trains for it, who hires."),
    ],
}


def build_next_moves(current_form: str, entry: dict, *,
                     soc: Optional[str] = None, top6: Optional[str] = None) -> list[NextMove]:
    """The typed catalog edges from the current node — the server owns the set,
    the model phrases them. Carries only the coordinate keys the edge declares."""
    moves: list[NextMove] = []
    for edge in EDGES.get(current_form, []):
        coord = coordinate_of(
            entry,
            soc=soc if "soc" in edge.carries else None,
            top6=top6 if "top6" in edge.carries else None,
        )
        moves.append(as_move(edge.target, coord, edge.rationale))
    return moves


# ── Salience vocabulary (§5.3: computed flags, never a reading of the numbers) ──

SAL_LOSSY_CROSSWALK = (
    "lossy-crosswalk: the TOP→CIP→SOC fan-out is wide here, so program↔occupation "
    "alignment is approximate.")
SAL_SMALL_N = (
    "small-n: the underlying counts are small; treat rates and medians cautiously.")
SAL_STALE_VINTAGE = (
    "stale-vintage: some figures predate the current cycle; state their as-of.")
SAL_PROJECTED_NOT_ACTUAL = (
    "supply=3yr-avg: supply is a 3-year average of DataMart completions (All Awards); "
    "the single most recent year (latest_year_supply) can run above or below it.")
SAL_MEMBER_ANCHORED = (
    "member-anchored: a generated member×sector view covers only occupations the member "
    "already serves with an active program — it does NOT surface greenfield demand in "
    "occupations the member does not yet serve. Absence here is not absence of regional demand.")
