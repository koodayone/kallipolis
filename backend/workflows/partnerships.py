import os
import re
import json
import logging
import anthropic
from ontology.schema import get_driver
from models import PartnershipProposal, CurriculumAlignment, ProposalList

logger = logging.getLogger(__name__)

PARTNERSHIP_PROMPT = """You are an institutional intelligence analyst for California community college workforce partnerships. Your job is to identify specific, actionable industry partnership opportunities between a community college and employers in its labor market region.

Below is the institutional context:

{context}

Based on this data, generate EXACTLY 6 partnership proposals. Each proposal must:
1. Name a specific employer from the list above (not a generic sector)
2. Identify 2-4 specific curricula by their EXACT names as listed above that align to that employer's job roles
3. Explain concretely which student populations benefit (e.g., "Healthcare Technology students in their second semester who have completed phlebotomy training")
4. Specify a concrete partnership type — exactly one of: Internship Pipeline, Apprenticeship Program, Advisory Board Seat, Guest Lecture Series, Equipment Donation & Lab Access, Co-op Employment, Tuition Reimbursement Compact, Hiring Commitment MOU
5. Provide a 2-3 sentence rationale that references specific job roles the employer needs and specific skills those curricula develop — be concrete, not generic

Make proposals specific, differentiated, and actionable. Each proposal should cover a different employer. Avoid generic language — name the exact skill, role, and outcome.

Return ONLY valid JSON with no text before or after, in this exact schema:

```json
{{
  "proposals": [
    {{
      "employer_or_sector": "string",
      "curriculum_alignment": [
        {{
          "program_name": "string",
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
        institution_records = session.run("""
            MATCH (i:Institution)-[:OFFERS]->(p:Program)-[:CONTAINS]->(c:Curriculum)
            RETURN i.name AS institution, i.region AS region,
                   p.name AS program, collect(c.name) AS curricula
            ORDER BY p.name
        """).data()

        employer_records = session.run("""
            MATCH (i:Institution)-[:LOCATED_IN]->(r:LaborMarketRegion)
                  <-[:OPERATES_IN]-(e:Employer)-[:REQUIRES]->(j:JobRole)
            RETURN e.name AS employer, e.sector AS sector,
                   collect(DISTINCT j.title) AS job_roles
            ORDER BY e.name
        """).data()

    lines = []

    if institution_records:
        lines.append(f"INSTITUTION: {institution_records[0]['institution']}")
        lines.append(f"LABOR MARKET REGION: {institution_records[0]['region']}")
        lines.append("")
        lines.append("PROGRAMS AND CURRICULA:")
        for record in institution_records:
            lines.append(f"\n  Program: {record['program']}")
            for c in sorted(record["curricula"]):
                lines.append(f"    - {c}")

    lines.append("")
    lines.append("EMPLOYERS IN THE REGION AND THEIR JOB ROLE NEEDS:")
    for record in employer_records:
        lines.append(f"\n  Employer: {record['employer']} (Sector: {record['sector']})")
        lines.append("  Job Roles Required:")
        for role in sorted(record["job_roles"]):
            lines.append(f"    - {role}")

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
                program_name=a["program_name"],
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
