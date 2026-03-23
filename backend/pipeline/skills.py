"""
Stage 2: Skill derivation pipeline.

Takes raw course data (SLOs, objectives, description) and uses Claude to
extract workforce-aligned skill_mappings. Normalizes against O*NET-derived
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

import anthropic

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

SYSTEM_PROMPT = """You are a workforce development specialist who maps community college course content to standardized skill categories.

Given a course's Student Learning Outcomes (SLOs), course objectives, and description, extract 3-6 skill categories that a student completing this course would develop.

RULES:
1. Prefer skills from the provided seed taxonomy when they fit. Use the EXACT name from the taxonomy.
2. If a course teaches something not well-captured by the seed taxonomy, you may introduce a new skill name. Keep it concise (2-4 words), specific, and workforce-relevant.
3. Focus on demonstrable, transferable competencies — not course topics.
4. Every skill should be something an employer or workforce board would recognize.
5. Return ONLY a JSON array of strings. No explanations.

SEED TAXONOMY:
{taxonomy}"""

USER_PROMPT = """Course: {code} — {name}
Department: {department}

Description:
{description}

Student Learning Outcomes:
{slos}

Course Objectives:
{objectives}

Extract 3-6 skill mappings as a JSON array:"""


CONCURRENCY = 3  # keep low to stay within 30K tokens/min rate limit
MAX_RETRIES = 5


async def _derive_single(
    client: anthropic.AsyncAnthropic,
    course: RawCourse,
    sem: asyncio.Semaphore,
) -> list[str]:
    """Derive skill_mappings for a single course with rate-limit retry."""
    slos = "\n".join(f"- {s}" for s in course.learning_outcomes) or "N/A"
    objectives = "\n".join(f"- {o}" for o in course.course_objectives[:10]) or "N/A"

    user_msg = USER_PROMPT.format(
        code=course.code,
        name=course.name,
        department=course.department,
        description=(course.description or "N/A")[:500],
        slos=slos,
        objectives=objectives,
    )

    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=256,
                    system=SYSTEM_PROMPT.format(taxonomy="\n".join(f"- {s}" for s in TAXONOMY_LIST)),
                    messages=[{"role": "user", "content": user_msg}],
                )

                text = response.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                skills = json.loads(text)
                if isinstance(skills, list) and all(isinstance(s, str) for s in skills):
                    logger.debug(f"{course.code}: {skills}")
                    return skills
                else:
                    logger.warning(f"Unexpected format for {course.code}: {text}")
                    return []
            except json.JSONDecodeError:
                logger.warning(f"JSON parse error for {course.code}: {text}")
                return []
            except anthropic.RateLimitError:
                wait = 2 ** attempt * 5  # 5, 10, 20, 40, 80 seconds
                logger.info(f"Rate limited on {course.code}, waiting {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
            except Exception as e:
                logger.error(f"Error deriving skills for {course.code}: {e}")
                return []

    logger.error(f"Exhausted retries for {course.code}")
    return []


async def derive_skills(courses: list[RawCourse]) -> list[dict]:
    """
    Derive skill_mappings for all courses using Claude.

    Returns a list of dicts (course data + skill_mappings).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    tasks = [_derive_single(client, c, sem) for c in courses]
    results = await asyncio.gather(*tasks)

    enriched = []
    novel_skills: set[str] = set()

    for course, skills in zip(courses, results):
        course_dict = course.to_dict()
        course_dict["skill_mappings"] = skills

        for skill in skills:
            if skill not in SEED_TAXONOMY:
                novel_skills.add(skill)

        enriched.append(course_dict)

    if novel_skills:
        logger.info(
            f"Novel skills discovered ({len(novel_skills)}): "
            + ", ".join(sorted(novel_skills))
        )

    return enriched
