"""
Stage 2: Skill derivation pipeline.

Takes raw course data (SLOs, objectives, description) and uses Gemini Flash
to extract workforce-aligned skill_mappings. Normalizes against the unified
skill taxonomy — a closed vocabulary connecting curriculum to labor markets.

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

# Unified skill taxonomy — the closed vocabulary for ALL skill assignment.
# Courses and occupations SELECT from this list; no invention allowed.
#
# Skills are the shared semantic terrain on which education and labor project
# different understandings of capability:
#   - Domain-centric terms (e.g., "Pharmacology", "Music Theory") preserve
#     educational and intellectual structure.
#   - Action-centric terms (e.g., "Patient Assessment", "Debugging") preserve
#     occupational and operational structure.
# No type label is stored — graph structure reveals how each skill functions.
UNIFIED_TAXONOMY = {
    # ── Healthcare: Clinical Practice (31) ────────────────────────────
    "Anatomy & Physiology",
    "Basic Life Support",
    "Clinical Documentation",
    "Dental Hygiene",
    "Dental Materials",
    "Diagnostic Imaging",
    "Drug Administration",
    "EKG Interpretation",
    "Emergency Response",
    "Geriatric Care",
    "Infection Control",
    "Medical Coding",
    "Medical Terminology",
    "Medication Administration",
    "Nursing Process",
    "Obstetric Care",
    "Oral Pathology",
    "Pathology",
    "Patient Assessment",
    "Patient Care",
    "Pediatric Care",
    "Pharmacology",
    "Phlebotomy",
    "Psychiatric Care",
    "Radiation Safety",
    "Radiographic Positioning",
    "Sterile Technique",
    "Surgical Assisting",
    "Triage",
    "Vital Signs",
    "Wound Care",
    # ── Healthcare: Therapy & Rehabilitation (10) ─────────────────────
    "Massage Therapy",
    "Mental Health",
    "Occupational Therapy",
    "Physical Therapy",
    "Prosthetics & Orthotics",
    "Rehabilitation",
    "Respiratory Therapy",
    "Speech Therapy",
    "Substance Abuse Counseling",
    "Treatment Planning",
    # ── Healthcare: Systems & Administration (6) ──────────────────────
    "Epidemiology",
    "Health Education",
    "Health Information Systems",
    "Medical Billing",
    "Nutrition",
    "Public Health",
    # ── Fitness & Athletics (8) ───────────────────────────────────────
    "Athletic Training",
    "Exercise Physiology",
    "Group Fitness Instruction",
    "Kinesiology",
    "Physical Fitness",
    "Sports Medicine",
    "Sports Performance",
    "Strength Training",
    # ── Trades: Electrical (8) ────────────────────────────────────────
    "Circuit Analysis",
    "Electrical Systems",
    "Electrical Wiring",
    "Motor Controls",
    "PLC Programming",
    "Power Distribution",
    "Solar Installation",
    "Telecommunications",
    # ── Trades: Mechanical & HVAC (8) ─────────────────────────────────
    "Diesel Systems",
    "Engine Repair",
    "HVAC Systems",
    "Hydraulics",
    "Mechanical Systems",
    "Pneumatics",
    "Refrigeration",
    "Troubleshooting",
    # ── Trades: Construction (14) ─────────────────────────────────────
    "Blueprint Reading",
    "Building Codes",
    "Carpentry",
    "Concrete Work",
    "Construction Methods",
    "Drywall",
    "Estimating",
    "Masonry",
    "Pipe Fitting",
    "Piping Systems",
    "Plumbing",
    "Rigging",
    "Roofing",
    "Structural Steel",
    # ── Trades: Manufacturing & Fabrication (12) ──────────────────────
    "CNC Programming",
    "Lean Manufacturing",
    "Machining",
    "Manufacturing",
    "Precision Measurement",
    "Quality Control",
    "Sheet Metal",
    "Soldering & Brazing",
    "Tool & Die",
    "Water Treatment",
    "Welding & Fabrication",
    "Woodworking",
    # ── Trades: Automotive (6) ────────────────────────────────────────
    "Auto Body Repair",
    "Automotive Repair",
    "Brake Systems",
    "Emissions Systems",
    "Engine Diagnostics",
    "Transmission Systems",
    # ── Computing: Software (12) ──────────────────────────────────────
    "Algorithms",
    "API Design",
    "Back-End Development",
    "Data Structures",
    "Debugging",
    "Front-End Development",
    "Mobile Development",
    "Object-Oriented Programming",
    "Programming",
    "Software Development",
    "Software Testing",
    "Version Control",
    # ── Computing: Infrastructure (10) ────────────────────────────────
    "Cloud Computing",
    "Computer Architecture",
    "Containerization",
    "Database Management",
    "DevOps",
    "Networking",
    "Operating Systems",
    "SQL",
    "Systems Administration",
    "Virtualization",
    # ── Computing: Security (5) ───────────────────────────────────────
    "Cybersecurity",
    "Digital Forensics",
    "Incident Response",
    "Network Security",
    "Penetration Testing",
    # ── Computing: Data & AI (6) ──────────────────────────────────────
    "Artificial Intelligence",
    "Business Intelligence",
    "Data Science",
    "Data Warehousing",
    "Machine Learning",
    "Web Development",
    # ── Computing: Design (4) ─────────────────────────────────────────
    "Game Design",
    "User Experience Design",
    "User Interface Design",
    "Web Design",
    # ── Arts: Visual (14) ─────────────────────────────────────────────
    "3D Modeling",
    "Animation",
    "Ceramics",
    "Color Theory",
    "Drawing",
    "Glasswork",
    "Illustration",
    "Jewelry Making",
    "Painting",
    "Photography",
    "Printmaking",
    "Sculpture",
    "Textile Arts",
    "Typography",
    # ── Arts: Design (8) ──────────────────────────────────────────────
    "Architectural Design",
    "Fashion Design",
    "Graphic Design",
    "Industrial Design",
    "Interior Design",
    "Landscape Architecture",
    "Sustainable Design",
    "Urban Planning",
    # ── Arts: Performing (12) ─────────────────────────────────────────
    "Acting",
    "Choreography",
    "Conducting",
    "Costume Design",
    "Ear Training",
    "Lighting Design",
    "Music Composition",
    "Music Theory",
    "Performing Arts",
    "Set Design",
    "Sound Design",
    "Stage Management",
    # ── Arts: Media Production (12) ───────────────────────────────────
    "Audio Production",
    "Broadcast Journalism",
    "Content Creation",
    "Digital Photography",
    "Documentary Production",
    "Film Production",
    "Multimedia Production",
    "Music Production",
    "Screenwriting",
    "Storyboarding",
    "Storytelling",
    "Video Production",
    # ── Arts: History & Theory (4) ────────────────────────────────────
    "Art History",
    "Creative Expression",
    "Film Analysis",
    "Music History",
    # ── Sciences: Life (10) ───────────────────────────────────────────
    "Anatomy",
    "Biochemistry",
    "Biology",
    "Biotechnology",
    "Cell Biology",
    "Ecology",
    "Genetics",
    "Microbiology",
    "Physiology",
    "Zoology",
    # ── Sciences: Physical (10) ───────────────────────────────────────
    "Astronomy",
    "Chemistry",
    "Environmental Science",
    "Geology",
    "Materials Science",
    "Meteorology",
    "Oceanography",
    "Organic Chemistry",
    "Physics",
    "Soil Science",
    # ── Sciences: Methods & Math (12) ─────────────────────────────────
    "Calculus",
    "Differential Equations",
    "Geospatial Analysis",
    "Laboratory Techniques",
    "Linear Algebra",
    "Mathematics",
    "Research Methods",
    "Scientific Methodology",
    "Spatial Reasoning",
    "Statistics",
    "Surveying",
    "Technical Drawing",
    # ── Language & Communication (10) ─────────────────────────────────
    "Academic Writing",
    "Argumentation",
    "Creative Writing",
    "Grammar",
    "Journalism",
    "Language Acquisition",
    "Public Speaking",
    "Rhetoric",
    "Sign Language",
    "Translation",
    # ── Humanities & Social Sciences (16) ─────────────────────────────
    "Anthropology",
    "Cultural Analysis",
    "Debate",
    "Economics",
    "Ethnic Studies",
    "Ethics",
    "Gender Studies",
    "Geography",
    "Historical Analysis",
    "Intercultural Communication",
    "International Relations",
    "Literary Analysis",
    "Philosophy",
    "Political Science",
    "Religious Studies",
    "Sociology",
    # ── Business: Finance & Accounting (12) ───────────────────────────
    "Accounting",
    "Auditing",
    "Banking",
    "Bookkeeping",
    "Budgeting",
    "Economics & Accounting",
    "Financial Analysis",
    "Financial Planning",
    "Insurance",
    "Investment",
    "Payroll",
    "Tax Preparation",
    # ── Business: Management & Operations (10) ────────────────────────
    "Administration & Management",
    "Contract Management",
    "Entrepreneurship",
    "Human Resources",
    "Labor Relations",
    "Operations Management",
    "Project Management",
    "Small Business Management",
    "Strategic Planning",
    "Supply Chain Management",
    # ── Business: Sales & Marketing (8) ───────────────────────────────
    "Customer Service",
    "Digital Marketing",
    "E-Commerce",
    "International Trade",
    "Market Research",
    "Negotiation",
    "Real Estate",
    "Sales & Marketing",
    # ── Business: Office & Administrative (6) ─────────────────────────
    "Clerical & Administrative",
    "Data Entry",
    "Document Management",
    "Office Technology",
    "Property Management",
    "Record Keeping",
    # ── Education (10) ────────────────────────────────────────────────
    "Assessment",
    "Child Development",
    "Classroom Management",
    "Curriculum Development",
    "Early Childhood Education",
    "Educational Technology",
    "Instructional Design",
    "Literacy Instruction",
    "Special Education",
    "Tutoring",
    # ── Social Services (10) ──────────────────────────────────────────
    "Case Management",
    "Community Engagement",
    "Conflict Resolution",
    "Counseling",
    "Crisis Intervention",
    "Diversity & Inclusion",
    "Psychology",
    "Restorative Justice",
    "Social Work",
    "Youth Development",
    # ── Public Safety: Law Enforcement (8) ────────────────────────────
    "Corrections",
    "Criminal Justice",
    "Emergency Dispatch",
    "Evidence Collection",
    "Forensic Science",
    "Investigation",
    "Law Enforcement",
    "Probation",
    # ── Public Safety: Fire & Emergency (6) ───────────────────────────
    "Arson Investigation",
    "Fire Science",
    "Fire Suppression",
    "Hazmat",
    "Rescue Operations",
    "Wildland Firefighting",
    # ── Agriculture & Natural Resources (16) ──────────────────────────
    "Agriculture",
    "Animal Husbandry",
    "Animal Science",
    "Aquaculture",
    "Arboriculture",
    "Enology",
    "Farm Management",
    "Floral Design",
    "Food Production",
    "Forestry",
    "Horticulture",
    "Irrigation Systems",
    "Landscape Design",
    "Pest Management",
    "Plant Science",
    "Viticulture",
    # ── Commercial Services: Culinary (8) ─────────────────────────────
    "Baking & Pastry",
    "Bartending",
    "Culinary Arts",
    "Food Safety",
    "Food Service Operations",
    "Kitchen Management",
    "Menu Planning",
    "Nutrition Science",
    # ── Commercial Services: Hospitality (5) ──────────────────────────
    "Event Planning",
    "Hospitality",
    "Hotel Management",
    "Tourism",
    "Travel Services",
    # ── Commercial Services: Personal Care (6) ────────────────────────
    "Barbering",
    "Cosmetology",
    "Esthetics",
    "Hair Styling",
    "Nail Technology",
    "Skin Care",
    # ── Commercial Services: Transportation (6) ───────────────────────
    "Aviation",
    "Flight Operations",
    "Logistics",
    "Maritime Operations",
    "Transportation",
    "Vehicle Operation",
    # ── Law (6) ───────────────────────────────────────────────────────
    "Contract Law",
    "Court Procedures",
    "Law & Government",
    "Legal Research",
    "Legal Writing",
    "Paralegal Studies",
    # ── Library & Information (3) ─────────────────────────────────────
    "Archival Science",
    "Information Literacy",
    "Library Science",
    # ── Cross-cutting: Technical (18) ─────────────────────────────────
    "Calibration",
    "Data Analysis",
    "Design",
    "Digital Literacy",
    "Engineering & Technology",
    "Equipment Operation",
    "Geographic Information Systems",
    "Inspection",
    "Materials Testing",
    "Mechanical",
    "OSHA Compliance",
    "Process Improvement",
    "Regulatory Compliance",
    "Safety Protocols",
    "Sustainability",
    "Systems Analysis",
    "Technical Writing",
    "Workplace Safety",
    # ── Cross-cutting: Professional (10) ──────────────────────────────
    "Leadership",
    "Mentoring",
    "Personnel Management",
    "Policy Analysis",
    "Professional Ethics",
    "Public Administration",
    "Public Safety & Security",
    "Risk Management",
    "Supervision",
    "Writing",
}

TAXONOMY_LIST = sorted(UNIFIED_TAXONOMY)

# Backwards-compatible aliases for downstream code
SEED_TAXONOMY = UNIFIED_TAXONOMY
TIER2_TAXONOMY = set()
TIER2_LIST = []
FULL_TAXONOMY = UNIFIED_TAXONOMY

SYSTEM_INSTRUCTION = """You are a workforce development specialist who maps community college course content to standardized skill categories.

Given courses with Student Learning Outcomes (SLOs), course objectives, and descriptions, extract at least 6 skill categories per course that a student completing the course would develop. Include every additional skill the course meaningfully develops.

RULES:
1. You MUST select skills from the provided taxonomy. Use the EXACT name from the taxonomy. ALL selected skills must come from the taxonomy — do not invent new skill names.
2. Focus on demonstrable, transferable competencies — not course topics or subtopics.
3. Every skill should be something an employer or workforce board would recognize.
4. Return ONLY a JSON object mapping each course code to its skill array. No explanations.

TAXONOMY:
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
    off_taxonomy: set[str] = set()
    unmapped = 0

    for course in courses:
        course_dict = course.to_dict()
        skills = all_mappings.get(course.code, [])
        if not skills:
            unmapped += 1
        course_dict["skill_mappings"] = skills

        for skill in skills:
            if skill not in UNIFIED_TAXONOMY:
                off_taxonomy.add(skill)

        enriched.append(course_dict)

    if unmapped:
        logger.warning(f"{unmapped} courses received no skill mappings")
    if off_taxonomy:
        logger.warning(
            f"Off-taxonomy skills returned ({len(off_taxonomy)}): "
            + ", ".join(sorted(off_taxonomy))
        )

    return enriched
