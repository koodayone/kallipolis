"""
Stage 2: Skill derivation pipeline.

Takes raw course data (SLOs, objectives, description) and uses Gemini Flash
to extract workforce-aligned skill_mappings. Normalizes against O*NET-derived
seed categories where possible.

Usage:
    from pipeline.skills import derive_skills
    enriched = await derive_skills(raw_courses)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import List

from google import genai
from google.genai import types

from pipeline.scraper import RawCourse

logger = logging.getLogger(__name__)

# O*NET-derived seed taxonomy — skills and knowledge areas most relevant
# to community college workforce development programs.
# These provide a normalization anchor; extracted skills that match these
# categories will use the canonical name.
SEED_TAXONOMY = {
    # O*NET Basic & Cross-Functional Skills
    "Active Learning",
    "Active Listening",
    "Complex Problem Solving",
    "Coordination",
    "Critical Thinking",
    "Instructing",
    "Judgment & Decision Making",
    "Management of Material Resources",
    "Management of Personnel Resources",
    "Mathematics",
    "Monitoring",
    "Negotiation",
    "Operations Analysis",
    "Oral Communication",
    "Persuasion",
    "Programming",
    "Quality Control Analysis",
    "Reading Comprehension",
    "Science",
    "Service Orientation",
    "Social Perceptiveness",
    "Systems Analysis",
    "Systems Evaluation",
    "Technology Design",
    "Time Management",
    "Troubleshooting",
    "Writing",
    # O*NET Knowledge Areas (workforce-relevant subset)
    "Administration & Management",
    "Biology",
    "Chemistry",
    "Clerical & Administrative",
    "Communications & Media",
    "Computers & Electronics",
    "Customer & Personal Service",
    "Design",
    "Economics & Accounting",
    "Education & Training",
    "Engineering & Technology",
    "English Language",
    "Food Production",
    "Geography",
    "Law & Government",
    "Mathematics & Statistics",
    "Mechanical",
    "Medicine & Dentistry",
    "Personnel & Human Resources",
    "Production & Processing",
    "Psychology",
    "Public Safety & Security",
    "Sales & Marketing",
    "Sociology & Anthropology",
    "Therapy & Counseling",
    "Transportation",
    # Domain-specific additions for CTE programs
    "Clinical Patient Care",
    "Health Information Systems",
    "Network & Cybersecurity",
    "Data Analysis & Visualization",
    "Regulatory Compliance",
    "Safety Protocols",
    "Digital Literacy",
    "Project Management",
    "Technical Writing",
    "Laboratory Techniques",
    "Equipment Operation & Maintenance",
    "Welding & Fabrication",
    "Electrical Systems",
    "Child Development & Pedagogy",
    "Financial Analysis",
    "Supply Chain Management",
    "Multimedia Production",
    "Geographic Information Systems",
    "Environmental Science",
}

TAXONOMY_LIST = sorted(SEED_TAXONOMY)

SYSTEM_INSTRUCTION = """You are a workforce development specialist who maps community college course content to standardized skill categories.

Given courses with Student Learning Outcomes (SLOs), course objectives, and descriptions, extract 3-6 skill categories per course that a student completing the course would develop.

RULES:
1. You MUST use skills from the provided seed taxonomy whenever possible. Use the EXACT name from the taxonomy. At least 2 of your selected skills per course should come from the taxonomy.
2. Only introduce a novel skill name if the course teaches something genuinely not covered by ANY taxonomy entry. Most courses can be fully described using taxonomy skills.
3. If you must introduce a novel skill, keep it broad and reusable (e.g., "Performing Arts" not "Advanced Singing Technique"), concise (2-4 words), and workforce-relevant.
4. Focus on demonstrable, transferable competencies — not course topics or subtopics.
5. Every skill should be something an employer or workforce board would recognize.
6. Return ONLY a JSON object mapping each course code to its skill array. No explanations.

SEED TAXONOMY:
{taxonomy}"""

SINGLE_COURSE_TEMPLATE = """---
Course: {code} — {name}
Department: {department}

Description:
{description}

Student Learning Outcomes:
{slos}

Course Objectives:
{objectives}"""

BATCH_USER_PROMPT = """{courses}

---
For each course above, extract 3-6 skill mappings. Return a JSON object mapping course code to skill array, e.g.:
{{"COURSE 101": ["Skill A", "Skill B"], "COURSE 102": ["Skill C", "Skill D"]}}"""


BATCH_SIZE = 8  # courses per API call
CONCURRENCY = 10
MAX_RETRIES = 5


def _format_course(course: RawCourse) -> str:
    """Format a single course for inclusion in a batched prompt."""
    slos = "\n".join(f"- {s}" for s in course.learning_outcomes) or "N/A"
    objectives = "\n".join(f"- {o}" for o in course.course_objectives[:10]) or "N/A"
    return SINGLE_COURSE_TEMPLATE.format(
        code=course.code,
        name=course.name,
        department=course.department,
        description=(course.description or "N/A")[:500],
        slos=slos,
        objectives=objectives,
    )


async def _derive_batch(
    client: genai.Client,
    batch: list[RawCourse],
    sem: asyncio.Semaphore,
) -> dict[str, list[str]]:
    """Derive skill_mappings for a batch of courses in a single Gemini call."""
    courses_text = "\n".join(_format_course(c) for c in batch)
    user_msg = BATCH_USER_PROMPT.format(courses=courses_text)

    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_msg,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION.format(
                            taxonomy="\n".join(f"- {s}" for s in TAXONOMY_LIST)
                        ),
                        max_output_tokens=8192,
                        temperature=0.2,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                    ),
                )

                text = response.text.strip()
                result = json.loads(text)
                if isinstance(result, dict) and all(
                    isinstance(v, list) and all(isinstance(s, str) for s in v)
                    for v in result.values()
                ):
                    codes = [c.code for c in batch]
                    logger.debug(f"Batch {codes[0]}..{codes[-1]}: {len(result)} courses mapped")
                    return result
                else:
                    logger.warning(f"Unexpected format for batch: {text[:200]}")
                    return {}
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error for batch: {e}. Response ends with: ...{text[-100:]}")
                return {}
            except Exception as e:
                error_str = str(e).lower()
                if "resource_exhausted" in error_str or "429" in error_str:
                    wait = 2 ** attempt * 5
                    logger.info(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Error deriving skills for batch: {e}")
                    return {}

    logger.error("Exhausted retries for batch")
    return {}


async def derive_skills(courses: list[RawCourse]) -> list[dict]:
    """
    Derive skill_mappings for all courses using Gemini Flash in batches.

    Sends BATCH_SIZE courses per API call to reduce cost and increase
    throughput. Returns a list of dicts (course data + skill_mappings).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")

    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    # Split courses into batches
    batches = [courses[i:i + BATCH_SIZE] for i in range(0, len(courses), BATCH_SIZE)]
    logger.info(f"Processing {len(courses)} courses in {len(batches)} batches of up to {BATCH_SIZE}")

    tasks = [_derive_batch(client, batch, sem) for batch in batches]
    batch_results = await asyncio.gather(*tasks)

    # Merge all batch results into a single code -> skills mapping
    all_mappings: dict[str, list[str]] = {}
    for result in batch_results:
        all_mappings.update(result)

    enriched = []
    novel_skills: set[str] = set()
    unmapped = 0

    for course in courses:
        course_dict = course.to_dict()
        skills = all_mappings.get(course.code, [])
        if not skills:
            unmapped += 1
        course_dict["skill_mappings"] = skills

        for skill in skills:
            if skill not in SEED_TAXONOMY:
                novel_skills.add(skill)

        enriched.append(course_dict)

    if unmapped:
        logger.warning(f"{unmapped} courses received no skill mappings")
    if novel_skills:
        logger.info(
            f"Novel skills discovered ({len(novel_skills)}): "
            + ", ".join(sorted(novel_skills))
        )

    return enriched
