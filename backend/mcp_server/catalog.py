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
            "'Supply' is COE PROJECTED completions (the gap denominator), not actual "
            "DataMart awards — never conflate them. The gap is REGIONAL; the institution's "
            "own supply is a separate figure (its share), never the gap itself."),
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
    "employer_shed": Form(
        id="employer_shed",
        question="Which regional employers hire for this occupation — who could the member convene?",
        meaning=(
            "The employer shed ranks regional employers by BLS OES staffing share for the "
            "target occupations — how prominently each employer's industry hires the role. "
            "It surfaces candidate partners, not a hiring roster."),
        guardrail=(
            "Ranked by OES industry staffing share; OES-suppressed cells are dropped (not "
            "marked), and the shortlist ('shown') is not the whole candidate pool ('total')."),
    ),
}


# ── The adjacency graph (§5.2: next-moves = catalog edges) ────────────────

@dataclass(frozen=True)
class Edge:
    target: str                 # the target form
    carries: tuple[str, ...]    # coordinate keys to carry forward (e.g. ("soc",))
    rationale: str


EDGES: dict[str, list[Edge]] = {
    "coverage": [
        Edge("gap", (), "Size the shortfall behind the coverage picture."),
        Edge("pathway", ("top6",), "Trace the selected program to the occupations it prepares for."),
    ],
    "gap": [
        Edge("employer_shed", ("soc",), "Identify regional employers to convene around the gapped occupation."),
        Edge("pathway", ("soc",), "See which programs feed the gapped occupation."),
    ],
    "pathway": [
        Edge("coverage", (), "Return to who covers this sector across the member's colleges."),
        Edge("employer_shed", ("soc",), "Find regional employers hiring for this occupation."),
    ],
    "employer_shed": [
        Edge("gap", (), "Quantify the supply–demand gap these employers face."),
        Edge("coverage", (), "See which colleges cover the occupations these employers hire."),
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
        moves.append(NextMove(form=edge.target, coordinate=coord, rationale=edge.rationale))
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
    "supply=projected≠actual: the gap uses COE projected completions, not actual awards.")
