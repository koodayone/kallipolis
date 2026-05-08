"""Deterministic templates for the occupation-centric partnership
opportunity report.

The narrative shape mirrors the employer-centric proposal in
``narrative_templates.py`` — same four data sections plus a new
Partnership Opportunities framing — but the prose is employer-agnostic.
The subject is the occupation and the regional labor market for it;
employers are positioned as the candidate target set surfaced by the
data, not the report's anchor.

Per the institutional-deference principle: every sentence is a
function of graph data + COE figures. Same college, same SOC always
yields byte-identical prose.

Public API:
    build_opportunity_narrative(...) -> dict[str, str]

Section names match the OpportunityReport model fields.
"""

from __future__ import annotations

# Reuse the formatting primitives from the existing module — they're
# style-bearing details we want consistent across both narrative
# surfaces during the transition.
from partnerships.narrative_templates import (
    fmt_are,
    fmt_count,
)


def build_executive_summary(
    *,
    college: str,
    soc_code: str,
    soc_title: str,
    sector_display: str,
    coe_region_display: str,
    total_aligned_courses: int,
    total_in_aligned_departments: int,
    n_employer_opportunities: int,
) -> str:
    """The two-sentence opportunity thesis, employer-agnostic.

    Sentence shapes:
        1. report-purpose opener — names what the report does upfront
           ("examines partnership opportunities in the X region for
           SOC Y, an occupation in the Z sector"). The SOC and sector
           are subordinated as appositives under the report's purpose
           rather than being the main clause. We deliberately do NOT
           add a qualitative demand qualifier ("active"/"modest"/etc.)
           here — past attempts used absolute openings thresholds
           (e.g. 50) that were arbitrary and region-blind. The
           Occupational Demand and LMI sections below carry the actual
           openings number.
        2. three-pillar partnership thesis in conditional mood
           ("Partnerships ... would be supported by"). The conditional
           mood is deliberate: the pillars are the basis for
           prospective partnership development, not evidence that
           partnerships already exist. Indicative ("are supported")
           would oversell. Pronoun variation across the three clauses
           ("for this occupation" → "for it" → "for this role") avoids
           the lazy thrice-repetition without sacrificing clarity.
    """
    # ES.1 — report-purpose opener with region + SOC + sector positioning.
    if sector_display and coe_region_display:
        s1 = (
            f"This report examines partnership opportunities in the "
            f"{coe_region_display} region for {soc_title} (SOC {soc_code}), "
            f"an occupation in the {sector_display} sector."
        )
    elif sector_display:
        s1 = (
            f"This report examines partnership opportunities for "
            f"{soc_title} (SOC {soc_code}), an occupation in the "
            f"{sector_display} sector."
        )
    elif coe_region_display:
        s1 = (
            f"This report examines partnership opportunities in the "
            f"{coe_region_display} region for {soc_title} (SOC {soc_code})."
        )
    else:
        s1 = (
            f"This report examines partnership opportunities for "
            f"{soc_title} (SOC {soc_code})."
        )

    # ES.2 — three-pillar partnership thesis in conditional mood, with
    # pronoun variation: "this occupation" → "for it" → "this role".
    course_phrase = fmt_count(total_aligned_courses, "course")
    student_phrase = fmt_count(total_in_aligned_departments, "student")
    employer_phrase = fmt_count(n_employer_opportunities, "regional employer")
    s2 = (
        f"Partnerships for this occupation would be supported by "
        f"{college}'s {course_phrase} that prepare for it, "
        f"{student_phrase} enrolled in programs that offer those courses, "
        f"and the {employer_phrase} that hire for this role."
    )

    return " ".join([s1, s2])


def build_occupational_demand(
    *,
    soc_code: str,
    soc_title: str,
    annual_wage: int | float | None,
    annual_openings: int | None,
    employment: int | None,
    growth_rate: float | None,
    coe_region_display: str,
) -> str:
    """Two-sentence regional-demand narrative for the SOC.

    Sentence shapes:
        1. wage + openings, attributed to Centers of Excellence
        2. current regional employment + 5-year projected growth

    Falls back gracefully when individual metrics are missing — the
    affected clause is dropped without breaking the surrounding prose.
    """
    region_in_phrase = (
        f"in the {coe_region_display} region" if coe_region_display else "regionally"
    )

    # Sentence 1: median wage and annual openings attributed to COE.
    parts: list[str] = []
    if annual_wage is not None:
        parts.append(f"earn a median annual wage of ${int(annual_wage):,}")
    if annual_openings is not None:
        opening_word = "opening" if int(annual_openings) == 1 else "openings"
        parts.append(f"{int(annual_openings):,} annual {opening_word}")
    if parts:
        # If both wage + openings present: "earn a median annual wage of $X
        # with N annual openings"; if only openings present: "have N annual
        # openings"; etc.
        if len(parts) == 2:
            demand_clause = f"{parts[0]} with {parts[1]}"
        elif annual_wage is not None:
            demand_clause = parts[0]
        else:
            demand_clause = f"have {parts[0]}"
        s1 = (
            f"According to the Centers of Excellence for Labor Market "
            f"Research, {soc_title} (SOC {soc_code}) {demand_clause} "
            f"{region_in_phrase}."
        )
    else:
        s1 = (
            f"According to the Centers of Excellence for Labor Market "
            f"Research, no wage or openings figures are published for "
            f"{soc_title} (SOC {soc_code}) {region_in_phrase}."
        )

    # Sentence 2: regional employment + projected growth.
    s2_parts: list[str] = []
    if employment is not None:
        s2_parts.append(
            f"{int(employment):,} workers are currently employed in the "
            "region with this occupational role"
        )
    if growth_rate is not None:
        sign = "+" if growth_rate >= 0 else ""
        pct = f"{sign}{growth_rate * 100:.1f}%"
        if s2_parts:
            s2_parts[0] += (
                f", with projected employment growth of {pct} over a "
                "5-year time span"
            )
        else:
            s2_parts.append(
                f"Projected employment growth for this role is {pct} "
                f"{region_in_phrase} over a 5-year time span"
            )
    s2 = (s2_parts[0] + ".") if s2_parts else ""

    return " ".join([s1, s2]).strip()


def build_curriculum_alignment(
    *,
    soc_code: str,
    soc_title: str,
    n_departments: int,
) -> str:
    """The two-sentence caption above the department-evidence table.

    Singular/plural agreement: when only one department aligns, both
    sentences switch to the singular form."""
    if n_departments == 1:
        s1 = (
            "According to the SOC-to-TOP institutional crosswalk maintained by "
            "the California Chancellor's Office, the program below prepares "
            f"students for SOC {soc_code}."
        )
        s2 = (
            "This program develops the core competencies required to perform "
            f"the role of {soc_title}."
        )
    else:
        s1 = (
            "According to the SOC-to-TOP institutional crosswalk maintained by "
            "the California Chancellor's Office, the programs below prepare "
            f"students for SOC {soc_code}."
        )
        s2 = (
            "These programs develop the core competencies required to perform "
            f"the role of {soc_title}."
        )
    return f"{s1} {s2}"


def build_student_impact(
    *,
    soc_code: str,
    total_in_aligned_departments: int,
) -> str:
    """The two-sentence caption above the candidate table.

    The candidate set is TOP4-aligned: students with coursework in the
    same 4-digit program family as the SOC's prep curriculum. Framed
    as the partnership-impacted pipeline rather than as already-
    prepared candidates — the partnership funds the routing through
    specific prep courses; the table surfaces who is in position to be
    routed.
    """
    student_phrase = fmt_count(total_in_aligned_departments, "student")
    s1 = (
        f"{student_phrase} {fmt_are(total_in_aligned_departments)} enrolled in "
        f"the programs whose courses align with SOC {soc_code}."
    )
    s2 = (
        "Shown below are students whose coursework sits in the same "
        "program family as the SOC's prep curriculum — the candidate "
        "pipeline a partnership would route into specific prep courses, "
        "ranked by depth of program-family enrollment then GPA."
    )
    return f"{s1} {s2}"


def build_partnership_opportunities(
    *,
    soc_title: str,
    n_employer_opportunities: int,
) -> str:
    """The caption framing the candidate-employer list as a multi-
    employer engagement opportunity rather than a sales target list.

    Authority chain: EDD ALMIS supplies the NAICS-4 classification for
    each employer (the scrape is parameterized by NAICS-4 code); BLS
    OEWS supplies the SOC × NAICS-4 employment-concentration figure
    used for ranking. Both authorities are named upfront — same
    paradigm as the LMI section's "According to the Centers of
    Excellence" opening.

    Empty case is honest about it — the report still carries value for
    program-development planning even with no immediate candidate
    employers in the regional market."""
    if n_employer_opportunities == 0:
        return (
            "No regional employers in the college's market currently surface "
            f"as candidate partners hiring for {soc_title}. The curriculum "
            "and student-pipeline evidence above remains a foundation for "
            "outbound partnership development in this occupational area."
        )
    employer_phrase = fmt_count(n_employer_opportunities, "regional employer")
    return (
        f"According to the Employment Development Department and the Bureau of "
        f"Labor Statistics, the {employer_phrase} shown below hire for "
        f"{soc_title} based on their NAICS codes. These industry partnership "
        f"candidates are sorted by how large a share of each NAICS industry's "
        f"workforce this role represents."
    )


def build_opportunity_narrative(
    *,
    college: str,
    sector_display: str,
    soc_code: str,
    soc_title: str,
    annual_wage: int | float | None,
    annual_openings: int | None,
    employment: int | None,
    growth_rate: float | None,
    coe_region_display: str,
    total_aligned_courses: int,
    n_departments: int,
    total_in_aligned_departments: int,
    n_employer_opportunities: int,
) -> dict:
    """Assemble the five narrative sections as a dict keyed to the
    OpportunityReport field names."""
    return {
        "executive_summary": build_executive_summary(
            college=college,
            soc_code=soc_code,
            soc_title=soc_title,
            sector_display=sector_display,
            coe_region_display=coe_region_display,
            total_aligned_courses=total_aligned_courses,
            total_in_aligned_departments=total_in_aligned_departments,
            n_employer_opportunities=n_employer_opportunities,
        ),
        "occupational_demand": build_occupational_demand(
            soc_code=soc_code,
            soc_title=soc_title,
            annual_wage=annual_wage,
            annual_openings=annual_openings,
            employment=employment,
            growth_rate=growth_rate,
            coe_region_display=coe_region_display,
        ),
        "curriculum_alignment": build_curriculum_alignment(
            soc_code=soc_code,
            soc_title=soc_title,
            n_departments=n_departments,
        ),
        "student_impact": build_student_impact(
            soc_code=soc_code,
            total_in_aligned_departments=total_in_aligned_departments,
        ),
        "partnership_opportunities": build_partnership_opportunities(
            soc_title=soc_title,
            n_employer_opportunities=n_employer_opportunities,
        ),
    }
