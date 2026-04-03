"""Three-stage partnership proposal pipeline: context → signal filter → narrative generation."""

import os
import re
import json
import logging
from collections import Counter, defaultdict
import anthropic
from ontology.schema import get_driver
from models import NarrativeProposal, Justification

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 2: Signal Filter
# ═══════════════════════════════════════════════════════════════════════════

_SIGNAL_FILTER_PROMPT = """You are evaluating skill-to-course alignment data from a community college's curriculum.

For each skill-to-course mapping below, assess whether the course genuinely develops the named skill based on the course name, department, and typical curriculum content.

A mapping is CREDIBLE when:
- The course content directly and obviously relates to the skill (e.g., "Accounting" → BUS 082 Introduction to Business)
- The department is a natural home for that skill (e.g., "Food Safety" → Food Services Work Experience)
- A program coordinator would look at this mapping and say "yes, that's real"

A mapping is NOT CREDIBLE when:
- The connection is incidental or metaphorical (e.g., "Strategic Planning" → Sports Medicine course)
- The skill name is being matched on surface-level word overlap rather than genuine content alignment (e.g., "Biology" → Psychology course)
- The course is a generic work experience placeholder being mapped to a specialized skill

Here is the raw alignment data:

{context}

Return a JSON object with two arrays:

{{
  "retained": [
    {{"skill": "...", "course_code": "...", "course_name": "...", "department": "...", "occupation": "...", "strength": "strong|moderate"}}
  ],
  "removed": [
    {{"skill": "...", "course_code": "...", "reason": "brief explanation"}}
  ]
}}

Rules:
- Be selective. It is better to retain 10 genuinely strong alignments than 40 where half are dubious.
- "strong" means direct occupational relevance. "moderate" means transferable skill with a reasonable connection.
- When the same skill appears multiple times across occupations, retain the single best course mapping.
- Return ONLY valid JSON with no text before or after."""


def _filter_context_signals(raw_context: str) -> str:
    """Stage 2: Filter raw context to retain only credible skill-to-course alignments.

    Returns a curated context string for the proposal generation stage.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": _SIGNAL_FILTER_PROMPT.format(context=raw_context)}],
    )
    raw_response = message.content[0].text

    # Parse filter output
    try:
        match = re.search(r"\{[\s\S]*\}", raw_response)
        if match:
            filter_result = json.loads(match.group(0))
        else:
            filter_result = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.warning("Signal filter returned invalid JSON, falling back to raw context")
        return raw_context

    retained = filter_result.get("retained", [])
    removed = filter_result.get("removed", [])

    logger.info(
        f"Signal filter: {len(retained)} retained, {len(removed)} removed"
    )
    for r in removed[:10]:
        logger.info(f"  Removed: {r.get('skill')} → {r.get('course_code')} ({r.get('reason', '')})")

    # Fallback: if everything was filtered, use raw context with a warning
    if not retained:
        logger.warning("Signal filter removed ALL alignments, falling back to raw context")
        return raw_context + "\n\nNOTE: Alignment quality for this employer-college pair is low. Be conservative in your claims."

    return _build_curated_context(raw_context, retained)


def _build_curated_context(raw_context: str, retained: list[dict]) -> str:
    """Reconstruct context string with only retained alignments."""
    lines = []

    # Extract employer header and student pipeline / economic data from raw context
    sections = raw_context.split("\n\n")
    for section in sections:
        stripped = section.strip()
        if stripped.startswith("EMPLOYER:") or stripped.startswith("College:"):
            lines.append(section)
        elif stripped.startswith("STUDENT PIPELINE:"):
            lines.append(section)
        elif stripped.startswith("ECONOMIC DATA"):
            lines.append(section)
        elif stripped.startswith("PARTNERSHIP ENGAGEMENT TYPE:"):
            lines.append(section)

    # Rebuild skill alignment section from retained alignments
    occ_groups: dict[str, list[dict]] = defaultdict(list)
    for entry in retained:
        occ_groups[entry.get("occupation", "Unknown")].append(entry)

    lines.append("")
    lines.append("CURATED SKILL ALIGNMENT BY OCCUPATION (pre-vetted for credibility):")
    for occ, entries in occ_groups.items():
        lines.append(f"\n  {occ}:")
        for e in entries:
            strength_tag = f" [{e.get('strength', 'moderate')}]" if e.get("strength") else ""
            lines.append(
                f"    - {e['skill']} → {e['course_code']} {e['course_name']} ({e['department']}){strength_tag}"
            )

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 1: Context Gathering (unchanged)
# ═══════════════════════════════════════════════════════════════════════════


def _gather_targeted_context(employer: str, college: str, engagement_type: str = "") -> str:
    """Gather employer-specific context from the graph for targeted proposal generation."""
    driver = get_driver()
    lines = []

    with driver.session() as session:
        # A. Employer overview
        emp_result = session.run("""
            MATCH (emp:Employer {name: $employer})
            OPTIONAL MATCH (emp)-[:IN_MARKET]->(r:Region)
            RETURN emp.name AS name, emp.sector AS sector, emp.description AS description,
                   collect(r.name) AS regions
        """, employer=employer).single()

        if not emp_result:
            raise ValueError(f"Employer '{employer}' not found in the graph.")

        lines.append(f"EMPLOYER: {emp_result['name']}")
        if emp_result["sector"]:
            lines.append(f"Sector: {emp_result['sector']}")
        if emp_result["description"]:
            lines.append(f"Description: {emp_result['description']}")
        if emp_result["regions"]:
            lines.append(f"Regions: {', '.join(emp_result['regions'])}")
        lines.append(f"College: {college}")

        # B. Skill alignment detail
        skill_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:IN_MARKET]->(r:Region),
                  (emp)-[:HIRES_FOR]->(occ:Occupation)<-[d:DEMANDS]-(r),
                  (occ)-[:REQUIRES_SKILL]->(sk:Skill)
            OPTIONAL MATCH (course:Course {college: $college})-[:DEVELOPS]->(sk)
            OPTIONAL MATCH (dept:Department)-[:CONTAINS]->(course)
            RETURN occ.title AS occupation, d.annual_wage AS annual_wage,
                   sk.name AS skill,
                   CASE WHEN course IS NOT NULL THEN true ELSE false END AS developed,
                   course.code AS course_code, course.name AS course_name,
                   dept.name AS department
        """, employer=employer, college=college).data()

        # Group by occupation
        occ_skills: dict[str, dict] = defaultdict(lambda: {"wage": None, "aligned": [], "gaps": []})
        for r in skill_result:
            occ = r["occupation"]
            occ_skills[occ]["wage"] = r["annual_wage"]
            if r["developed"] and r["course_code"]:
                occ_skills[occ]["aligned"].append({
                    "skill": r["skill"],
                    "course_code": r["course_code"],
                    "course_name": r["course_name"],
                    "department": r["department"] or "Unknown",
                })
            else:
                occ_skills[occ]["gaps"].append(r["skill"])

        lines.append("")
        lines.append("SKILL ALIGNMENT BY OCCUPATION:")
        total_aligned = 0
        total_gaps = 0
        for occ, data in occ_skills.items():
            wage_str = f" (${data['wage']:,}/yr)" if data["wage"] else ""
            lines.append(f"\n  {occ}{wage_str}:")
            if data["aligned"]:
                lines.append("    Aligned Skills (college develops these):")
                # Deduplicate by skill name
                seen = set()
                for entry in data["aligned"]:
                    if entry["skill"] not in seen:
                        seen.add(entry["skill"])
                        lines.append(f"      - {entry['skill']} → {entry['course_code']} {entry['course_name']} ({entry['department']})")
                        total_aligned += 1
            if data["gaps"]:
                unique_gaps = list(dict.fromkeys(data["gaps"]))
                lines.append("    Skill Gaps (employer needs, college does NOT develop):")
                for gap in unique_gaps:
                    lines.append(f"      - {gap}")
                    total_gaps += 1

        lines.append(f"\nSUMMARY: {total_aligned} aligned skills, {total_gaps} skill gaps across {len(occ_skills)} occupations.")

        # C. Student pipeline
        pipeline_result = session.run("""
            MATCH (emp:Employer {name: $employer})-[:HIRES_FOR]->(occ:Occupation)
                  -[:REQUIRES_SKILL]->(sk:Skill)<-[:HAS_SKILL]-(st:Student)
            WHERE EXISTS { (st)-[:ENROLLED_IN]->(:Course {college: $college}) }
            WITH DISTINCT st, collect(DISTINCT sk.name) AS student_skills
            OPTIONAL MATCH (st)-[e:ENROLLED_IN]->(c:Course {college: $college})
            WHERE e.grade IN ['A','B','C','P']
            WITH st, student_skills, count(DISTINCT c) AS completed
            RETURN count(st) AS total_students,
                   sum(CASE WHEN completed >= 3 THEN 1 ELSE 0 END) AS deep_pipeline,
                   reduce(all_skills = [], s IN collect(student_skills) | all_skills + s) AS flat_skills
        """, employer=employer, college=college).single()

        if pipeline_result and pipeline_result["total_students"] > 0:
            # Count top skills
            skill_counter = Counter()
            for s in pipeline_result["flat_skills"]:
                skill_counter[s] += 1
            top_pipeline_skills = [s for s, _ in skill_counter.most_common(5)]

            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append(f"  Total students with relevant skills: {pipeline_result['total_students']}")
            lines.append(f"  Students with 3+ completed courses: {pipeline_result['deep_pipeline']}")
            if top_pipeline_skills:
                lines.append(f"  Top skills in pipeline: {', '.join(top_pipeline_skills)}")
        else:
            lines.append("")
            lines.append("STUDENT PIPELINE:")
            lines.append("  Total students with relevant skills: 0")
            lines.append("  Students with 3+ completed courses: 0")

        # D. Regional employment
        econ_result = session.run("""
            MATCH (:College {name: $college})-[:IN_MARKET]->(r:Region)-[d:DEMANDS]->(occ:Occupation)
                  <-[:HIRES_FOR]-(emp:Employer {name: $employer})
            RETURN occ.title AS title, d.annual_wage AS annual_wage,
                   d.employment AS employment, d.growth_rate AS growth_rate,
                   d.annual_openings AS annual_openings, r.name AS region
        """, employer=employer, college=college).data()

        if econ_result:
            lines.append("")
            lines.append("ECONOMIC DATA (regional employment, wages, and demand projections):")
            for r in econ_result:
                wage = f"${r['annual_wage']:,}/yr" if r["annual_wage"] else "wage unavailable"
                emp_count = f"{r['employment']:,} employed" if r["employment"] else "employment data unavailable"
                parts = [f"{r['title']} in {r['region']}: {wage}, {emp_count}"]
                if r.get("growth_rate") is not None:
                    parts.append(f"{r['growth_rate']:+.1%} growth (2024-2029)")
                if r.get("annual_openings") is not None:
                    parts.append(f"{r['annual_openings']:,} annual openings")
                lines.append(f"  {', '.join(parts)}")

    if engagement_type:
        lines.append("")
        lines.append(f"PARTNERSHIP ENGAGEMENT TYPE: {engagement_type}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Stage 3: Proposal Generation Prompts
# ═══════════════════════════════════════════════════════════════════════════

_NARRATIVE_PREAMBLE = """You are a workforce partnership analyst writing an internal decision-support brief for a California community college program coordinator.

Below is curated institutional context for a specific employer. Every alignment listed has been pre-vetted for credibility — use all of them. Do not invent alignments, course codes, student counts, or wage figures not present in the context.

{context}

Write a partnership proposal as a single JSON object with this exact schema:

{{
  "summary": "<3-4 sentences>",
  "justification": {{
    "student_composition": "<one paragraph>",
    "course_composition": "<one paragraph>",
    "occupational_demand": "<one paragraph>"
  }},
  "roadmap": "<one paragraph>"
}}

Section requirements:
- SUMMARY: Frame what the partnership is, then make the career pathway case — cite specific entry-level occupations with wages, openings, and growth rates, and show how they extend into higher-earning roles. End with the regional demand signal (total employment across the employer's occupations).
- JUSTIFICATION — Student Composition: Ground in pipeline size and skills concentration. Connect the strongest student skills to the employer's operational needs.
- JUSTIFICATION — Course Composition: Cite specific departments, course codes, and the skills they develop. Address skill gaps constructively — frame them as opportunities rather than deficiencies. Lead with the strongest alignment clusters.
- JUSTIFICATION — Occupational Demand: Cite specific occupations with wages, employment counts, growth rates, and annual openings. Identify entry-level vs. advancement pathways.
- ROADMAP: Propose directional next steps — specific enough to act on this week (name departments, course sequences, cohort sizes, timelines) but not overly prescriptive. Do not write a project plan.

Style:
- Write for a knowledgeable reader who will spot generic filler instantly. Every sentence should contain a specific data point or a concrete recommendation.
- Be concise. Each justification paragraph should be 3-5 sentences.
- Do not use bullet points or numbered lists inside the JSON string values. Write in flowing prose.
- Return ONLY valid JSON with no text before or after."""


INTERNSHIP_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Internship Pipeline — structured student work rotations at the employer site.

Type-specific guidance for the proposal:
- The summary should frame this as placing students in rotations that connect to a career pathway.
- The roadmap should reference identifying operational areas for rotations, defining a rotation duration (8-16 weeks typical), mapping to existing Work Experience course sequences for academic credit, and setting a first-cohort target.
- Think about which departments and courses naturally produce students ready for on-site rotations at this specific employer.

REFERENCE EXAMPLE (match this level of specificity and narrative quality — do not copy its content):

Summary: An internship pipeline between College of the Sequoias and Cargill would place students in structured rotations across Cargill's food production and agricultural operations in the Central Valley. The partnership positions students toward a career pathway that starts with accessible entry points — Food Science Technicians ($47,950/yr, 190 annual openings, +2.5% growth) and Agricultural Inspectors ($57,160/yr, 90 annual openings) — and extends into high-earning management roles such as Industrial Production Managers ($115,380/yr, +6.6% growth) and General & Operations Managers ($101,990/yr, 2,240 annual openings, +8.4% growth). The college's existing programs in agriculture, food services, and business align directly with this pathway, and the Central Valley's concentration of over 46,000 employed workers across Cargill's hiring occupations signals sustained regional demand.

Justification — Student Composition: College of the Sequoias has over 15,000 students with skills relevant to Cargill's hiring needs, with approximately 14,500 having completed three or more courses in aligned programs. The strongest concentration of relevant skills in the pipeline includes research methods, data analysis, and professional ethics — foundational competencies that map to Cargill's quality control, food safety, and regulatory compliance requirements across multiple occupational categories.

Justification — Course Composition: The college develops 48 skills that Cargill's workforce requires, with the most credible alignment concentrated in a few departments. Agriculture Business Management (AGMT 103) directly develops supply chain management knowledge relevant to Cargill's production operations. The Food Services Work Experience sequence (WEXP 193DD, WEXP 196D) develops food production and food safety skills that map to Cargill's food science technician and agricultural inspector roles. The Business department (BUS 082, BUS 295, BUS 297) provides accounting, bookkeeping, and financial literacy that align with Cargill's accounting and auditing functions. The college's only notable skill gaps are auditing and labor relations — specialized competencies that are more appropriately developed through on-site experience during internship rotations.

Justification — Occupational Demand: Cargill hires across 8 occupations in the Central Valley–Mother Lode region, with combined regional employment exceeding 46,000 positions. The most accessible entry points for interns are Food Science Technicians (1,260 employed, 190 annual openings, $47,950/yr) and Agricultural Inspectors (560 employed, 90 annual openings, $57,160/yr). For students progressing into management pathways, Industrial Production Managers ($115,380/yr, 190 annual openings) and General & Operations Managers ($101,990/yr, 2,240 annual openings, +8.4% growth) represent substantial upward mobility within the same employer.

Roadmap: The first step is to convene an introductory meeting between the Agriculture and Business department chairs and Cargill's Central Valley site leadership to identify 2–3 operational areas suitable for student rotations — food quality labs, agricultural field inspection, and production floor operations are natural starting points given the curriculum alignment. From there, the college and Cargill should jointly define a 12–16 week rotation structure that maps to the existing Work Experience course sequence (WEXP series), allowing students to earn academic credit while gaining supervised industry exposure. The target for a first cohort would be 8–12 students placed in rotations within two semesters, with a feedback loop between Cargill site supervisors and faculty liaisons to refine the placement model for subsequent terms."""


CURRICULUM_CODESIGN_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Curriculum Co-Design — the employer shapes program content and quality through ongoing collaboration with faculty.

Type-specific guidance for the proposal:
- The summary should frame this as a faculty-industry collaboration to close skill gaps and modernize curriculum.
- The course composition section is the most important pillar for this type — lead with the specific skill gaps the collaboration would address, and which courses or programs would be redesigned.
- The roadmap should reference convening a faculty-industry working group, conducting a curriculum gap audit against the employer's skill needs, piloting revised course content, and establishing a review cadence (e.g., quarterly).
- Frame skill gaps as the primary motivation — this partnership type exists because the employer needs skills the college doesn't yet develop.

REFERENCE EXAMPLE (match this level of specificity and narrative quality — do not copy its content):

Summary: A curriculum co-design partnership between College of the Sequoias and Cargill would bring Cargill's operational expertise into the college's program development process, targeting the specific skill gaps that separate current graduates from Cargill's hiring requirements. The collaboration would focus on closing gaps in auditing and labor relations — skills required across Cargill's Accountants and Auditors ($80,560/yr, 940 annual openings) and Human Resources Specialists ($73,550/yr, 650 annual openings, +7.2% growth) roles — while strengthening existing course content in food safety, quality control, and supply chain management to better reflect current industry practice. With over 46,000 workers employed across Cargill's occupations in the Central Valley and sustained growth projected across all eight hiring categories, aligning curriculum to this employer's standards positions graduates for a labor market with deep and expanding demand.

Justification — Student Composition: The college has over 15,000 students with skills relevant to Cargill's workforce needs, with approximately 14,500 having completed three or more courses in aligned programs. The pipeline's strongest skill concentrations — research methods, data analysis, and professional ethics — indicate that students are developing foundational competencies, but the curriculum co-design would ensure these competencies are calibrated to the specific rigor and application standards Cargill expects in its quality control, compliance, and management functions.

Justification — Course Composition: The college's existing curriculum covers a broad range of Cargill's skill requirements, but two notable gaps — auditing and labor relations — represent skills that no current course develops, despite being required by Cargill's Accountants and Auditors and Human Resources Specialists roles respectively. The co-design collaboration would audit the Business department's course sequence (BUS 082, BUS 295, BUS 297) to identify where auditing concepts could be integrated into existing coursework, and evaluate whether the Social Sciences or Business programs could incorporate labor relations content. Beyond gap closure, the partnership would modernize existing aligned courses: the Food Services Work Experience sequence (WEXP 193DD, WEXP 196D) could be updated to reflect Cargill's current food safety protocols, and Agriculture Business Management (AGMT 103) could incorporate case studies from Cargill's Central Valley supply chain operations.

Justification — Occupational Demand: Cargill's hiring spans 8 occupations in the Central Valley–Mother Lode region with combined employment exceeding 46,000 positions. The roles most affected by curriculum gaps are Accountants and Auditors (10,780 employed, $80,560/yr, +4.7% growth) and Human Resources Specialists (6,590 employed, $73,550/yr, +7.2% growth) — both high-volume, growing occupations where closing even one skill gap meaningfully improves graduate competitiveness. The broader occupation portfolio, including Industrial Production Managers ($115,380/yr) and General & Operations Managers ($101,990/yr, +8.4% growth), ensures that curriculum improvements benefit students across multiple career pathways within the same employer.

Roadmap: The first step is to convene a faculty-industry working group with representatives from the Business and Agriculture departments and Cargill's Central Valley HR and operations leadership, with the initial meeting focused on a structured curriculum gap audit — mapping Cargill's skill requirements against current course learning outcomes to identify specific content additions. From there, the working group should prioritize 2–3 courses for pilot revision in the next catalog cycle, with Cargill contributing industry-current case studies, assessment criteria, or guest instruction modules. A quarterly review cadence would allow the working group to evaluate whether revised content is producing measurable improvement in student preparedness, with the goal of closing both identified skill gaps within two academic years."""


ADVISORY_BOARD_PROMPT = _NARRATIVE_PREAMBLE + """

PARTNERSHIP TYPE: Advisory Board — ongoing strategic guidance from the employer to inform program direction.

Type-specific guidance for the proposal:
- The summary should frame this as establishing a structured channel for industry insight into program decisions.
- This partnership is relationship-based and does NOT require SWP or other grant funding. Do not reference grant applications or funding mechanisms.
- The roadmap should reference sending a formal invitation, scheduling an inaugural meeting, preparing an initial agenda grounded in the data (skill gaps, industry trends), and setting a meeting cadence (quarterly is standard).
- The course composition section should identify which departments the board would advise — scope it to areas with the strongest alignment.
- Initial agenda topics should be grounded in specific skill gaps or curriculum questions from the data.

REFERENCE EXAMPLE (match this level of specificity and narrative quality — do not copy its content):

Summary: An advisory board partnership with Cargill would give College of the Sequoias a structured channel for industry guidance on its Agriculture, Business, and Food Services programs — the departments most directly aligned with Cargill's Central Valley operations. With Cargill hiring across 8 occupations in the region representing over 46,000 employed workers, the advisory relationship would ensure the college's program direction stays calibrated to a major regional employer whose roles span from entry-level Food Science Technicians ($47,950/yr, +2.5% growth) through General & Operations Managers ($101,990/yr, 2,240 annual openings, +8.4% growth). This is a relationship-based partnership that requires no grant funding — its value is in the ongoing dialogue between faculty and industry leadership.

Justification — Student Composition: The college has over 15,000 students developing skills relevant to Cargill's hiring needs, with approximately 14,500 having completed three or more courses in aligned programs. An advisory board would help the college understand whether the skills these students are developing — particularly research methods, data analysis, and professional ethics — meet the current standard Cargill expects, and where emerging industry trends might require the college to evolve its program emphasis.

Justification — Course Composition: The strongest alignment between the college and Cargill is concentrated in three departments: Agriculture (AGMT 103 develops supply chain management), Food Services (WEXP 193DD, WEXP 196D develop food production and food safety), and Business (BUS 082, BUS 295, BUS 297 develop accounting, bookkeeping, and financial analysis). These departments would form the natural scope for the advisory board. Two specific skill gaps — auditing and labor relations — would be immediate agenda items, as Cargill can advise on whether these gaps are best addressed through new coursework, modifications to existing courses, or alternative pathways like industry certifications.

Justification — Occupational Demand: Cargill's regional presence spans occupations with strong and growing demand: Agricultural Inspectors (560 employed, 90 annual openings, +2.2% growth), Food Science Technicians (1,260 employed, 190 annual openings, +2.5% growth), and a management tier including Industrial Production Managers ($115,380/yr, +6.6% growth) and Marketing Managers ($129,110/yr, +6.4% growth). The advisory board would provide the college with direct insight into how hiring patterns, skill requirements, and technology adoption are shifting across these roles — intelligence that is difficult to obtain from labor market data alone.

Roadmap: The first step is to send a formal invitation to Cargill's Central Valley site or regional leadership, proposing a quarterly advisory board scoped to the Agriculture, Business, and Food Services programs. The inaugural meeting agenda should be grounded in the data: a review of the college's current curriculum alignment with Cargill's skill requirements, a discussion of the auditing and labor relations skill gaps, and an open conversation about emerging workforce trends in food production and agricultural operations. The target is to hold the first meeting within one semester, with a standing quarterly cadence thereafter and a lightweight feedback mechanism — such as a brief survey or structured debrief — to ensure each meeting produces actionable guidance for faculty."""


PROMPTS: dict[str, str] = {
    "internship": INTERNSHIP_PROMPT,
    "curriculum_codesign": CURRICULUM_CODESIGN_PROMPT,
    "advisory_board": ADVISORY_BOARD_PROMPT,
}


# ═══════════════════════════════════════════════════════════════════════════
# Parsing & Pipeline
# ═══════════════════════════════════════════════════════════════════════════


def _parse_narrative_proposal(raw: str, employer: str, sector: str | None = None) -> NarrativeProposal:
    """Parse Claude's response into a NarrativeProposal."""
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    # Extract JSON from response
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        json_str = match.group(1).strip()
    else:
        match = re.search(r"```\s*([\s\S]*?)\s*```", raw)
        if match:
            json_str = match.group(1).strip()
        else:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                json_str = match.group(0).strip()
            else:
                json_str = raw.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}\nRaw: {raw[:800]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")

    return NarrativeProposal(
        employer=employer,
        sector=sector,
        partnership_type=data.get("partnership_type", ""),
        summary=data["summary"],
        justification=Justification(**data["justification"]),
        roadmap=data["roadmap"],
    )


def _get_employer_sector(employer: str) -> str | None:
    """Look up the employer's sector from the graph."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (e:Employer {name: $name}) RETURN e.sector AS sector",
            name=employer,
        ).single()
    return result["sector"] if result else None


def _get_prompt(engagement_type: str, context: str) -> str:
    """Select and format the type-specific prompt template."""
    template = PROMPTS.get(engagement_type, INTERNSHIP_PROMPT)
    return template.format(context=context)


def _call_claude(prompt_text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    )
    return message.content[0].text


async def run_targeted_proposal(employer: str, college: str, engagement_type: str = "") -> NarrativeProposal:
    """Generate a targeted partnership proposal for a specific employer."""
    sector = _get_employer_sector(employer)
    raw_context = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    curated_context = _filter_context_signals(raw_context)
    logger.info(f"Stage 2 complete: filtered signals for {employer}")

    prompt_text = _get_prompt(engagement_type, curated_context)
    raw = _call_claude(prompt_text)
    logger.info("Stage 3 complete: Claude response received, parsing proposal...")

    proposal = _parse_narrative_proposal(raw, employer, sector)
    # Ensure partnership_type is set from engagement type if not in response
    if not proposal.partnership_type:
        type_labels = {
            "internship": "Internship Pipeline",
            "curriculum_codesign": "Curriculum Co-Design",
            "advisory_board": "Advisory Board",
        }
        proposal.partnership_type = type_labels.get(engagement_type, engagement_type)
    logger.info(f"Parsed narrative proposal for {employer}.")
    return proposal


def stream_targeted_proposal(employer: str, college: str, engagement_type: str = ""):
    """Generator that yields a NarrativeProposal when Claude's streaming response completes."""
    sector = _get_employer_sector(employer)
    raw_context = _gather_targeted_context(employer, college, engagement_type)
    logger.info(f"Stage 1 complete: gathered context for {employer}")

    curated_context = _filter_context_signals(raw_context)
    logger.info(f"Stage 2 complete: filtered signals for {employer}")

    prompt_text = _get_prompt(engagement_type, curated_context)
    logger.info(f"Stage 3: starting Claude stream for {employer} ({engagement_type})...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt_text}],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

    proposal = _parse_narrative_proposal(accumulated, employer, sector)
    # Ensure partnership_type is set
    if not proposal.partnership_type:
        type_labels = {
            "internship": "Internship Pipeline",
            "curriculum_codesign": "Curriculum Co-Design",
            "advisory_board": "Advisory Board",
        }
        proposal.partnership_type = type_labels.get(engagement_type, engagement_type)
    logger.info(f"Stream complete: narrative proposal for {employer}")
    yield proposal
