import os
import re
import json
import logging
from collections import Counter
import anthropic
from ontology.schema import get_driver
from models import PartnershipProposal, CurriculumAlignment, ProposalList

logger = logging.getLogger(__name__)

PARTNERSHIP_PROMPT = """You are an institutional intelligence analyst for California community college workforce partnerships. Your job is to identify specific, actionable industry partnership opportunities between a community college and employers in its labor market region.

Below is the institutional context — departments are summarized with their key workforce skills and representative courses:

{context}

Based on this data, generate EXACTLY 3 partnership proposals. Each proposal must:
1. Name a specific employer from the list above (not a generic sector)
2. Identify 2-4 departments whose courses develop skills aligned to that employer's job roles, referencing the skills and representative courses listed
3. Explain concretely which student populations benefit, referencing the student pipeline data (number of students, completion depth, and concentrated skills) where available
4. Specify a concrete partnership type — exactly one of: Internship Pipeline, Apprenticeship Program, Advisory Board Seat, Guest Lecture Series, Equipment Donation & Lab Access, Co-op Employment, Tuition Reimbursement Compact, Hiring Commitment MOU
5. Provide a 2-3 sentence rationale that references specific job roles, the skills those departments develop, and the size of the student pipeline that makes this partnership viable

Make proposals specific, differentiated, and actionable. Each proposal should cover a different employer. Avoid generic language — name the exact skill, role, and outcome.

Return ONLY valid JSON with no text before or after, in this exact schema:

```json
{{
  "proposals": [
    {{
      "employer_or_sector": "string",
      "curriculum_alignment": [
        {{
          "department_name": "string",
          "curriculum_name": "string",
          "relevance_note": "string"
        }}
      ],
      "student_population_relevance": "string",
      "partnership_type": "string",
      "rationale": "string"
    }}
  ]
}}
```"""


def _gather_context() -> str:
    driver = get_driver()
    with driver.session() as session:
        # Summarize departments with course counts, skills, and sample courses
        institution_records = session.run("""
            MATCH (i:Institution)-[:OFFERS]->(d:Department)-[:CONTAINS]->(c:Course)
            WITH i, d, count(c) AS course_count,
                 collect(c.skill_mappings) AS all_skill_arrays,
                 collect(c.name) AS course_names
            RETURN i.name AS institution, i.region AS region,
                   d.name AS department, course_count,
                   course_names[0..5] AS sample_courses,
                   all_skill_arrays
            ORDER BY course_count DESC
        """).data()

        employer_records = session.run("""
            MATCH (i:Institution)-[:LOCATED_IN]->(r:LaborMarketRegion)
                  <-[:OPERATES_IN]-(e:Employer)-[:REQUIRES]->(j:JobRole)
            RETURN e.name AS employer, e.sector AS sector,
                   collect(DISTINCT j.title) AS job_roles
            ORDER BY e.name
        """).data()

        # Student pipeline: aggregate students per department with skills
        student_pipeline = session.run("""
            MATCH (s:Student)-[e:ENROLLED_IN]->(c:Course)
            WHERE e.status = 'Completed' AND c.department IS NOT NULL
            WITH c.department AS dept, s,
                 collect(DISTINCT c.code) AS completed_codes,
                 reduce(skills = [], sk IN collect(c.skill_mappings) | skills + sk) AS all_skills
            WITH dept, s, completed_codes, all_skills
            WITH dept,
                 count(DISTINCT s) AS total_students,
                 sum(CASE WHEN size(completed_codes) >= 3 THEN 1 ELSE 0 END) AS deep_pipeline,
                 collect(all_skills) AS nested_skills
            RETURN dept, total_students, deep_pipeline, nested_skills
            ORDER BY total_students DESC
        """).data()

    lines = []

    if institution_records:
        lines.append(f"INSTITUTION: {institution_records[0]['institution']}")
        lines.append(f"LABOR MARKET REGION: {institution_records[0]['region']}")
        lines.append("")
        lines.append("DEPARTMENTS (summarized with key workforce skills):")
        for record in institution_records:
            # Flatten skill arrays and find top 5
            skill_counter = Counter()
            for skill_list in record["all_skill_arrays"]:
                if skill_list:
                    skill_counter.update(skill_list)
            top_skills = [s for s, _ in skill_counter.most_common(5)]

            lines.append(f"\n  Department: {record['department']} ({record['course_count']} courses)")
            if top_skills:
                lines.append(f"    Key Skills: {', '.join(top_skills)}")
            if record["sample_courses"]:
                lines.append(f"    Sample Courses: {', '.join(record['sample_courses'][:5])}")

    lines.append("")
    lines.append("EMPLOYERS IN THE REGION AND THEIR JOB ROLE NEEDS:")
    for record in employer_records:
        lines.append(f"\n  Employer: {record['employer']} (Sector: {record['sector']})")
        lines.append("  Job Roles Required:")
        for role in sorted(record["job_roles"]):
            lines.append(f"    - {role}")

    # Student pipeline section
    if student_pipeline:
        lines.append("")
        lines.append("STUDENT WORKFORCE PIPELINE (active students with completed coursework):")
        for record in student_pipeline:
            if record["total_students"] < 10:
                continue
            dept = record["dept"]
            total = record["total_students"]
            deep = record["deep_pipeline"]

            # Flatten nested skill arrays and count
            skill_counter = Counter()
            for skill_list in record["nested_skills"]:
                if skill_list:
                    for skill in skill_list:
                        skill_counter[skill] += 1
            top_skills = skill_counter.most_common(5)

            lines.append(f"\n  {dept}: {total} students ({deep} with 3+ courses completed)")
            if top_skills:
                skill_str = ", ".join(f"{s} ({c})" for s, c in top_skills)
                lines.append(f"    Top Skills by Student Count: {skill_str}")

    return "\n".join(lines)


def _call_claude(context: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": PARTNERSHIP_PROMPT.format(context=context),
        }],
    )
    return message.content[0].text


def _parse_proposals(raw: str) -> list[PartnershipProposal]:
    logger.info(f"Claude raw response (first 300 chars): {raw[:300]!r}")

    # Strategy 1: extract from ```json ... ``` code block
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        json_str = match.group(1).strip()
    else:
        # Strategy 2: extract from generic ``` ... ``` code block
        match = re.search(r"```\s*([\s\S]*?)\s*```", raw)
        if match:
            json_str = match.group(1).strip()
        else:
            # Strategy 3: find JSON object directly in response
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                json_str = match.group(0).strip()
            else:
                json_str = raw.strip()

    logger.info(f"Attempting to parse JSON string (first 200 chars): {json_str[:200]!r}")

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}\nRaw: {raw[:800]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")

    proposals = []
    for item in data.get("proposals", []):
        alignment = [
            CurriculumAlignment(
                department_name=a["department_name"],
                curriculum_name=a["curriculum_name"],
                relevance_note=a["relevance_note"],
            )
            for a in item.get("curriculum_alignment", [])
        ]
        proposals.append(PartnershipProposal(
            employer_or_sector=item["employer_or_sector"],
            curriculum_alignment=alignment,
            student_population_relevance=item["student_population_relevance"],
            partnership_type=item["partnership_type"],
            rationale=item["rationale"],
        ))
    return proposals


async def run_partnerships() -> ProposalList:
    context = _gather_context()
    logger.info("Gathered graph context, calling Claude...")
    raw = _call_claude(context)
    logger.info("Claude response received, parsing proposals...")
    proposals = _parse_proposals(raw)
    logger.info(f"Parsed {len(proposals)} proposals.")
    return ProposalList(proposals=proposals)


# ── Streaming support ──────────────────────────────────────────────────────────


def _try_extract_next_proposal(
    accumulated: str, already_found: int
) -> "PartnershipProposal | None":
    """
    Try to extract the (already_found + 1)th complete proposal object
    from the accumulated JSON stream.
    """
    # Find the start of the proposals array
    array_start = accumulated.find('"proposals"')
    if array_start == -1:
        return None
    bracket_pos = accumulated.find("[", array_start)
    if bracket_pos == -1:
        return None

    # Walk through the text after the opening bracket, tracking brace depth
    # to find complete {...} objects
    pos = bracket_pos + 1
    found = 0

    while pos < len(accumulated):
        # Skip whitespace and commas
        while pos < len(accumulated) and accumulated[pos] in " \t\n\r,":
            pos += 1

        if pos >= len(accumulated) or accumulated[pos] != "{":
            break

        # Found start of an object — track brace depth to find its end
        obj_start = pos
        depth = 0
        in_string = False
        escape_next = False

        while pos < len(accumulated):
            ch = accumulated[pos]
            if escape_next:
                escape_next = False
            elif ch == "\\":
                escape_next = True
            elif ch == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        # Complete object found
                        obj_str = accumulated[obj_start : pos + 1]
                        if found == already_found:
                            try:
                                item = json.loads(obj_str)
                                alignment = [
                                    CurriculumAlignment(
                                        department_name=a["department_name"],
                                        curriculum_name=a["curriculum_name"],
                                        relevance_note=a.get("relevance_note", ""),
                                    )
                                    for a in item.get("curriculum_alignment", [])
                                ]
                                return PartnershipProposal(
                                    employer_or_sector=item["employer_or_sector"],
                                    curriculum_alignment=alignment,
                                    student_population_relevance=item[
                                        "student_population_relevance"
                                    ],
                                    partnership_type=item["partnership_type"],
                                    rationale=item["rationale"],
                                )
                            except (json.JSONDecodeError, KeyError):
                                return None
                        found += 1
                        pos += 1
                        break
            pos += 1
        else:
            # Reached end of accumulated text without closing the object
            return None

    return None


def stream_partnerships():
    """
    Generator that yields PartnershipProposal objects as they complete
    during Claude's streaming response.
    """
    context = _gather_context()
    logger.info("Gathered graph context, starting Claude stream...")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    accumulated = ""
    proposal_count = 0

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": PARTNERSHIP_PROMPT.format(context=context),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            accumulated += text

            # Check if a new complete proposal has appeared
            while True:
                proposal = _try_extract_next_proposal(accumulated, proposal_count)
                if proposal is None:
                    break
                proposal_count += 1
                logger.info(f"Streamed proposal {proposal_count}: {proposal.employer_or_sector}")
                yield proposal

    # Fallback: if streaming detection missed any, parse full response
    try:
        all_proposals = _parse_proposals(accumulated)
        for p in all_proposals[proposal_count:]:
            proposal_count += 1
            logger.info(f"Fallback proposal {proposal_count}: {p.employer_or_sector}")
            yield p
    except Exception:
        pass

    logger.info(f"Stream complete: {proposal_count} proposals.")
