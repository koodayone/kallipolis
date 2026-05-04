"""Deterministic templates for the partnership proposal narrative.

Replaces the LLM-driven prose-shaping in ``narrative.py`` with pure
Python templates over the data already gathered from the institutional
graph. Every sentence is a function of (employer record, selected
occupation, supply/demand evidence, curriculum evidence, student
stats) — no model call at runtime.

Architectural arc this completes:

    C2 (commit history): retired the LLM occupation picker
    C3:                  retired the LLM department-relevance filter
    *here*:              retire the LLM narrative writer

The single LLM-derived input is ``employer.operations_summary``, a
pre-computed verb phrase populated at ingestion by
``employers.characterize`` (one Gemini call per employer, ~$0.000024,
stored on the Employer node). At runtime, the narrative is purely a
function of graph data: same employer, same college, same SOC always
yields byte-identical prose. Two coordinators looking at the same
proposal see the same artifact.

Public API:
    build_executive_summary(...)  — 4 sentences, ~80 words
    build_occupational_demand(...) — 2 sentences
    build_curriculum_alignment(...) — 2 sentences
    build_student_impact(...)      — 2 sentences

Each is a pure function: same inputs always yield the same output.
The narrative dict assembled by these is the same shape the LLM
formerly produced, so ``_assemble_proposal`` is unchanged.
"""

from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════
# Formatting primitives
#
# These are the load-bearing details. Every stylistic decision the
# institutional voice depends on lives here. Templates compose them;
# they don't reinvent them.
# ═══════════════════════════════════════════════════════════════════════════


def fmt_count(n: int, singular: str, plural: str | None = None) -> str:
    """Render ``N noun`` with correct plural and thousands separator.

    Examples:
        fmt_count(0, "student")       → "0 students"
        fmt_count(1, "student")       → "1 student"
        fmt_count(13038, "student")   → "13,038 students"
        fmt_count(1, "course")        → "1 course"
        fmt_count(354, "course")      → "354 courses"

    Use ``plural`` for irregular nouns where adding "s" is wrong
    (no current cases in the templates, but reserved for safety).
    """
    word = singular if n == 1 else (plural or singular + "s")
    return f"{n:,} {word}"


def fmt_have(n: int) -> str:
    """``"has"`` for n == 1, ``"have"`` otherwise. Verb agreement for the
    count subject in the executive summary's pipeline-proof sentence."""
    return "has" if n == 1 else "have"


def fmt_are(n: int) -> str:
    """``"is"`` for n == 1, ``"are"`` otherwise. Verb agreement for the
    student-impact opener."""
    return "is" if n == 1 else "are"


def fmt_wage(wage: int | float | None) -> str:
    """Format a median annual wage figure for prose use.

    Returns either ``"a median annual wage of $99,490"`` for a real
    figure or ``"unreported median annual wage"`` for a missing one.
    The phrase is meant to slot into ``"an occupation with {…}"``.
    """
    if wage is None:
        return "unreported median annual wage"
    return f"a median annual wage of ${int(wage):,}"


def fmt_openings(openings: int | None) -> str:
    """Format an annual-openings figure for prose use.

    Returns ``"1,470 annual openings"`` or ``"unreported annual
    openings"``. Slots into ``"... and {…} in the {region} region"``.
    """
    if openings is None:
        return "unreported annual openings"
    return f"{int(openings):,} annual opening{'' if int(openings) == 1 else 's'}"


def fmt_demand_clause(wage: int | float | None, openings: int | None) -> str:
    """Compose the wage + openings clause used in OD.1.

    Cases:
        wage + openings present:
            "an occupation with a median annual wage of $X and N annual openings"
        wage missing, openings present:
            "an occupation with N annual openings"
        wage present, openings missing:
            "an occupation with a median annual wage of $X"
        both missing:
            "an occupation"

    Returning the noun-phrase ``"an occupation [with ...]"`` lets the
    caller append the regional attribution cleanly: ``f"{clause} in
    the {region} region according to Centers of Excellence projections."``.
    """
    parts = []
    if wage is not None:
        parts.append(fmt_wage(wage))
    if openings is not None:
        parts.append(fmt_openings(openings))
    if not parts:
        return "an occupation"
    return "an occupation with " + " and ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# Section builders
# ═══════════════════════════════════════════════════════════════════════════


def build_executive_summary(
    *,
    employer_name: str,
    operations_summary: str,
    sector_display: str,
    college: str,
    soc_code: str,
    total_aligned_courses: int,
    total_in_aligned_departments: int,
) -> str:
    """The four-sentence partnership thesis.

    Sentence shapes:
        1. employer characterization (operations_summary; falls back to
           a sector-only structural sentence if the employer hasn't
           been characterized yet)
        2. partnership thesis (template; uses "this role" rather than a
           role-specific noun phrase, since SOC is named in ES.3)
        3. curriculum proof (course count + SOC)
        4. student pipeline proof (deduped student count in aligned
           departments)
    """
    # ES.1 — employer characterization
    if operations_summary:
        s1 = f"{employer_name} {operations_summary}."
    else:
        # Fallback when an employer in the graph predates characterize.py
        # or had an empty description. Keeps the proposal generative
        # rather than failing; the resulting prose is honestly less
        # specific but never wrong.
        sector_phrase = f"{sector_display} sector" if sector_display else "workforce"
        s1 = f"{employer_name} operates in the {sector_phrase}."

    # ES.2 — partnership thesis (purely template; same shape every time).
    # "the employer's hiring needs" rather than "the college's hiring needs":
    # the partnership thesis is that the *college* helps fill the *employer's*
    # workforce demand, not the other way around. The original LLM-authored
    # prose used the pronoun "its" with the most recent noun (the employer)
    # as antecedent, but pronoun reference is fragile in templates — we name
    # the role explicitly here.
    s2 = (
        f"{college} can partner with {employer_name} to fulfill the employer's "
        "hiring needs for this role by leveraging the college's institutional assets."
    )

    # ES.3 — curriculum proof
    course_phrase = fmt_count(total_aligned_courses, "course")
    s3 = (
        f"The college offers {course_phrase} with TOP codes that map to "
        f"SOC {soc_code}, the target occupation for this partnership."
    )

    # ES.4 — student pipeline proof
    student_phrase = fmt_count(total_in_aligned_departments, "student")
    s4 = (
        f"{student_phrase} {fmt_have(total_in_aligned_departments)} taken courses in the "
        "departments offering these courses, indicating a talent pool that "
        "can be sourced to fulfill labor market demand."
    )

    return " ".join([s1, s2, s3, s4])


def build_occupational_demand(
    *,
    employer_name: str,
    soc_code: str,
    soc_title: str,
    annual_wage: int | float | None,
    annual_openings: int | None,
    coe_region_display: str,
) -> str:
    """Single-sentence regional-demand framing for the SELECTED
    occupation only. Cites COE-region figures (never national,
    cross-occupation, or aggregate). The Curriculum Alignment section
    that follows is the dedicated place for naming aligned courses
    and departments; this section stays focused on demand."""

    demand_clause = fmt_demand_clause(annual_wage, annual_openings)
    return (
        f"{employer_name}'s core hiring centers on {soc_title} (SOC {soc_code}), "
        f"{demand_clause} in the {coe_region_display} region according to "
        "Centers of Excellence projections."
    )


def build_curriculum_alignment(
    *,
    employer_name: str,
    soc_code: str,
    soc_title: str,
    n_departments: int,
) -> str:
    """The two-sentence caption above the department-evidence table.

    Singular/plural agreement: when only one department aligns, both
    sentences switch to the singular form ("the department below
    prepares ...", "This department develops ...") rather than reading
    "departments" with a one-row table."""
    if n_departments == 1:
        s1 = (
            "According to the SOC-to-TOP institutional crosswalk maintained by "
            "the California Chancellor's Office, the department below prepares "
            f"students for SOC {soc_code}."
        )
        s2 = (
            "This department develops the core competencies required to perform "
            f"the role of {soc_title} at {employer_name}."
        )
    else:
        s1 = (
            "According to the SOC-to-TOP institutional crosswalk maintained by "
            "the California Chancellor's Office, the departments below prepare "
            f"students for SOC {soc_code}."
        )
        s2 = (
            "These departments develop the core competencies required to perform "
            f"the role of {soc_title} at {employer_name}."
        )
    return f"{s1} {s2}"


def build_student_impact(
    *,
    soc_code: str,
    total_in_aligned_departments: int,
) -> str:
    """The two-sentence caption above the candidate table.

    First sentence cites the headline pipeline figure scoped to the
    aligned departments; second sentence is a fixed table-pointer."""
    student_phrase = fmt_count(total_in_aligned_departments, "student")
    s1 = (
        f"{student_phrase} {fmt_are(total_in_aligned_departments)} enrolled in the "
        f"departments containing TOP codes that align with SOC {soc_code}."
    )
    s2 = (
        "Shown below are students that are most strongly prepared with the "
        "coursework included in the TOP-SOC crosswalk."
    )
    return f"{s1} {s2}"


# ═══════════════════════════════════════════════════════════════════════════
# Composition
# ═══════════════════════════════════════════════════════════════════════════


def build_narrative(
    *,
    employer_name: str,
    operations_summary: str,
    sector_display: str,
    college: str,
    soc_code: str,
    soc_title: str,
    annual_wage: int | float | None,
    annual_openings: int | None,
    coe_region_display: str,
    total_aligned_courses: int,
    total_in_aligned_departments: int,
    n_departments: int,
) -> dict:
    """Assemble the four narrative sections as a dict. Same shape the
    LLM formerly produced, so ``_assemble_proposal`` is unchanged."""
    return {
        "executive_summary": build_executive_summary(
            employer_name=employer_name,
            operations_summary=operations_summary,
            sector_display=sector_display,
            college=college,
            soc_code=soc_code,
            total_aligned_courses=total_aligned_courses,
            total_in_aligned_departments=total_in_aligned_departments,
        ),
        "occupational_demand": build_occupational_demand(
            employer_name=employer_name,
            soc_code=soc_code,
            soc_title=soc_title,
            annual_wage=annual_wage,
            annual_openings=annual_openings,
            coe_region_display=coe_region_display,
        ),
        "curriculum_alignment": build_curriculum_alignment(
            employer_name=employer_name,
            soc_code=soc_code,
            soc_title=soc_title,
            n_departments=n_departments,
        ),
        "student_impact": build_student_impact(
            soc_code=soc_code,
            total_in_aligned_departments=total_in_aligned_departments,
        ),
    }
