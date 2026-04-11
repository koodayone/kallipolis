"""
Stage 1+2 (PDF): Extract course data AND skill mappings from a college catalog
PDF using Gemini Flash.

Optimized pipeline:
  1. Split PDF into small page-range chunks (not send full PDF every call)
  2. Pre-filter pages using text heuristics to skip non-course content
  3. Extract courses + derive skills in a single LLM call

Usage:
    from pipeline.scraper_pdf import scrape_pdf_catalog
    courses = await scrape_pdf_catalog(
        pdf_url="https://laney.edu/hubfs/2025-2026%20Catalog_FINAL_rev2_8.18.25.pdf",
        college_key="laney",
    )
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from google import genai
from google.genai import types
from pypdf import PdfReader, PdfWriter

from pipeline.scraper import RawCourse
from pipeline.skills import UNIFIED_TAXONOMY

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent / "cache"

# ── Config ────────────────────────────────────────────────────────────────────

PAGES_PER_BATCH = 25  # pages per Gemini call (smaller = less output truncation)
CONCURRENCY = 5       # concurrent Gemini calls (lighter per-call now)
MAX_RETRIES = 5

# Regex to detect course code patterns on a page (e.g., "ENGL 1A", "BUS 010")
COURSE_CODE_PATTERN = re.compile(
    r'\b[A-Z]{2,6}\s+\d{1,4}[A-Z]?\b'
)

# Minimum course code matches on a page to consider it a course description page
MIN_CODES_PER_PAGE = 2

TAXONOMY_LIST = sorted(UNIFIED_TAXONOMY)

SYSTEM_INSTRUCTION = """You are a structured data extraction and workforce skills specialist for community college course catalogs.

You will receive pages from a college course catalog PDF. Extract EVERY course you find and derive workforce skill mappings for each.

For each course, extract:
- code: The course code/number (e.g., "ENGL 1A", "CIS 1", "BIOL 10A"). Include the department prefix and number.
- name: The full course title
- department: The department or discipline name (e.g., "English", "Computer Information Systems", "Biology")
- units: Number of units as a string (e.g., "3", "4", "1.5-3")
- description: The course description paragraph
- prerequisites: Prerequisites/corequisites text, or empty string if none listed
- learning_outcomes: Array of Student Learning Outcomes (SLOs) if listed, otherwise empty array
- course_objectives: Array of course objectives if listed, otherwise empty array
- transfer_status: Transfer status (e.g., "CSU/UC", "CSU", "") if mentioned
- ge_area: General education area if listed, otherwise empty string
- grading: Grading method if listed (e.g., "Letter Grade", "Pass/No Pass"), otherwise empty string
- hours: Lecture/lab hours if listed, otherwise empty string
- skill_mappings: Array of workforce skill categories (at least 6) derived from the course description, SLOs, and objectives

COURSE EXTRACTION RULES:
1. ONLY extract courses from COURSE DESCRIPTION sections — where you see a course code, title, units, and a prose description paragraph. Do NOT extract from program requirement tables, degree/certificate requirement lists, or curriculum guides that only list course codes, titles, and units in a tabular format without descriptions.
2. Extract ALL courses from course description sections. Do not skip any.
3. If a field is not present in the catalog, use empty string "" or empty array [].
4. Course codes should preserve the exact format used in the catalog.
5. Do not fabricate or infer information that isn't on the page.
6. If no course descriptions are found on these pages, return an empty array [].
7. Department should be the broad discipline name, not the full program title.

SKILL MAPPING RULES:
1. You MUST select skills from this taxonomy. Use EXACT names: {taxonomy}
2. Select ALL skills from the taxonomy that the course meaningfully develops. Do NOT invent new skill names.
3. Focus on demonstrable, transferable competencies — not course topics.
4. If the course has no description, return an empty skill_mappings array.

Return ONLY a JSON array of course objects. No explanations or markdown."""

USER_PROMPT = """Extract all courses from these pages with skill mappings.

Return a JSON array where each element has these fields:
{{"code": "...", "name": "...", "department": "...", "units": "...", "description": "...", "prerequisites": "...", "learning_outcomes": [...], "course_objectives": [...], "transfer_status": "...", "ge_area": "...", "grading": "...", "hours": "", "skill_mappings": ["Skill A", "Skill B", ...]}}

Remember: return ONLY the JSON array, no other text."""


# ── PDF utilities ─────────────────────────────────────────────────────────────

async def _download_pdf(url: str, college_key: str) -> Path:
    """Download catalog PDF, caching locally."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = CACHE_DIR / f"{college_key}_catalog.pdf"

    if pdf_path.exists():
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        logger.info(f"Using cached PDF: {pdf_path} ({size_mb:.1f} MB)")
        return pdf_path

    logger.info(f"Downloading catalog PDF from {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/pdf,*/*",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()

    pdf_path.write_bytes(response.content)
    size_mb = len(response.content) / (1024 * 1024)
    logger.info(f"Downloaded {size_mb:.1f} MB → {pdf_path}")
    return pdf_path


def _filter_course_pages(pdf_path: Path) -> list[int]:
    """
    Identify pages that likely contain course descriptions using text heuristics.

    Returns 0-indexed page numbers that have enough course code patterns to
    suggest they contain course description content (not just program tables
    or general info).
    """
    reader = PdfReader(pdf_path)
    course_pages = []

    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            continue

        # Count course code pattern matches
        matches = COURSE_CODE_PATTERN.findall(text)
        if len(matches) >= MIN_CODES_PER_PAGE:
            # Additional heuristic: course description pages typically have
            # prose text (longer lines), not just tabular data
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            long_lines = sum(1 for line in lines if len(line) > 80)
            if long_lines >= 2:
                course_pages.append(i)

    return course_pages


def _split_pdf_pages(pdf_path: Path, page_indices: list[int], tmp_dir: str) -> Path:
    """Write a subset of pages from a PDF into a new temporary PDF file."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for idx in page_indices:
        writer.add_page(reader.pages[idx])

    chunk_path = Path(tmp_dir) / f"chunk_{page_indices[0]}_{page_indices[-1]}.pdf"
    with open(chunk_path, "wb") as f:
        writer.write(f)

    return chunk_path


# ── Gemini extraction ─────────────────────────────────────────────────────────

# Sentinels (distinct from empty results)
_TRUNCATED = "__TRUNCATED__"
_RATE_LIMITED = "__RATE_LIMITED__"

# Consecutive 429s before aborting the entire college
RATE_LIMIT_ABORT_THRESHOLD = 5


class RateLimitAbort(Exception):
    """Raised when too many consecutive 429s indicate quota exhaustion."""
    pass


async def _extract_batch(
    client: genai.Client,
    chunk_path: Path,
    page_label: str,
    sem: asyncio.Semaphore,
    rate_limit_counter: dict,
) -> list[dict] | str:
    """
    Extract courses + skills from a small PDF chunk using Gemini Flash.

    Returns list of course dicts on success, empty list if no courses found,
    _TRUNCATED if output was truncated, or _RATE_LIMITED if quota exhausted.
    """

    for attempt in range(MAX_RETRIES):
        # Check if other batches have already tripped the abort threshold
        if rate_limit_counter["consecutive"] >= RATE_LIMIT_ABORT_THRESHOLD:
            return _RATE_LIMITED

        async with sem:
            try:
                uploaded = client.files.upload(file=chunk_path)

                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        uploaded,
                        USER_PROMPT,
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION.format(
                            taxonomy=", ".join(TAXONOMY_LIST)
                        ),
                        max_output_tokens=65536,
                        temperature=0.1,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                    ),
                )

                # Success — reset the rate limit counter
                rate_limit_counter["consecutive"] = 0

                text = response.text.strip()
                result = json.loads(text)

                if isinstance(result, list):
                    valid = [c for c in result if isinstance(c, dict) and c.get("code")]
                    logger.info(f"  {page_label}: extracted {len(valid)} courses")
                    return valid
                else:
                    logger.warning(f"  {page_label}: unexpected format (not array)")
                    return []

            except json.JSONDecodeError as e:
                logger.warning(f"  {page_label}: JSON truncated — will retry with smaller chunks")
                return _TRUNCATED
            except Exception as e:
                error_str = str(e).lower()
                if "resource_exhausted" in error_str or "429" in error_str:
                    rate_limit_counter["consecutive"] += 1
                    if rate_limit_counter["consecutive"] >= RATE_LIMIT_ABORT_THRESHOLD:
                        logger.error(
                            f"  {page_label}: hit {RATE_LIMIT_ABORT_THRESHOLD} consecutive "
                            f"429s — aborting college (API quota exhausted)"
                        )
                        return _RATE_LIMITED
                    wait = 2 ** attempt * 5
                    logger.info(f"  Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"  {page_label}: error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        return []

    logger.error(f"  {page_label}: exhausted retries")
    return []


# ── Post-processing ───────────────────────────────────────────────────────────

def _deduplicate_courses(all_courses: list[dict]) -> list[dict]:
    """Deduplicate courses by code, keeping the most complete entry."""
    seen: dict[str, dict] = {}

    for course in all_courses:
        code = course.get("code", "").strip()
        if not code:
            continue

        if code not in seen:
            seen[code] = course
        else:
            existing = seen[code]
            existing_score = sum(1 for v in existing.values() if v)
            new_score = sum(1 for v in course.values() if v)
            if new_score > existing_score:
                seen[code] = course

    return list(seen.values())


def _to_raw_course(course_dict: dict) -> RawCourse:
    """Convert an extracted dict to a RawCourse, normalizing fields."""
    return RawCourse(
        code=str(course_dict.get("code", "")).strip(),
        name=str(course_dict.get("name", "")).strip(),
        department=str(course_dict.get("department", "")).strip(),
        units=str(course_dict.get("units", "")).strip(),
        description=re.sub(r'\s+\d{4}\.\d{2}\s*$', '', str(course_dict.get("description", ""))).strip(),
        prerequisites=str(course_dict.get("prerequisites", "")).strip(),
        learning_outcomes=_ensure_str_list(course_dict.get("learning_outcomes", [])),
        course_objectives=_ensure_str_list(course_dict.get("course_objectives", [])),
        transfer_status=str(course_dict.get("transfer_status", "")).strip(),
        ge_area=str(course_dict.get("ge_area", "")).strip(),
        grading=str(course_dict.get("grading", "")).strip(),
        hours=str(course_dict.get("hours", "")).strip(),
        url="",
    )


def _ensure_str_list(val) -> list[str]:
    """Ensure a value is a list of strings."""
    if isinstance(val, list):
        return [str(item).strip() for item in val if str(item).strip()]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _to_enriched_dict(course_dict: dict) -> dict:
    """Convert extracted dict to enriched format (RawCourse fields + skill_mappings)."""
    raw = _to_raw_course(course_dict)
    d = raw.to_dict()
    d["skill_mappings"] = _ensure_str_list(course_dict.get("skill_mappings", []))
    return d


# ── Main entry point ──────────────────────────────────────────────────────────

async def scrape_pdf_catalog(
    pdf_url: str,
    college_key: str,
    pages_per_batch: int = PAGES_PER_BATCH,
) -> list[RawCourse]:
    """
    Download a college catalog PDF, extract courses + skills using Gemini Flash.

    Optimized flow:
      1. Download PDF (cached)
      2. Pre-filter pages to identify course description content
      3. Split into small PDF chunks (only course pages)
      4. Send each chunk to Gemini for combined extraction + skill derivation
      5. Deduplicate and return

    Returns:
        List of RawCourse objects (skill_mappings stored in enriched cache)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")

    # Step 1: Download PDF
    pdf_path = await _download_pdf(pdf_url, college_key)

    # Step 2: Pre-filter pages
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    logger.info(f"Catalog has {total_pages} pages. Filtering for course content...")

    course_pages = _filter_course_pages(pdf_path)

    # Fallback: if filtering returns <10% of pages, the PDF likely uses
    # non-extractable text (image-based, unusual encoding). Send all pages.
    min_expected = max(10, int(total_pages * 0.10))
    if len(course_pages) < min_expected:
        logger.warning(
            f"Filtering found only {len(course_pages)} pages (expected ≥{min_expected}). "
            f"PDF may be image-based — falling back to all pages."
        )
        course_pages = list(range(total_pages))

    logger.info(
        f"Processing {len(course_pages)} pages out of {total_pages} "
        f"({100 * len(course_pages) / total_pages:.0f}% of catalog)"
    )

    # Step 3: Split into chunks and send to Gemini
    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    # Group consecutive course pages into batches
    batches: list[list[int]] = []
    current_batch: list[int] = []
    for page_idx in course_pages:
        current_batch.append(page_idx)
        if len(current_batch) >= pages_per_batch:
            batches.append(current_batch)
            current_batch = []
    if current_batch:
        batches.append(current_batch)

    logger.info(f"Processing {len(course_pages)} pages in {len(batches)} batches")

    # Shared counter: if consecutive 429s hit the threshold, all batches abort
    rate_limit_counter = {"consecutive": 0}

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Initial extraction pass
        chunk_tasks = []
        for batch_pages in batches:
            chunk_path = _split_pdf_pages(pdf_path, batch_pages, tmp_dir)
            label = f"pages {batch_pages[0]+1}-{batch_pages[-1]+1}"
            chunk_tasks.append((batch_pages, _extract_batch(client, chunk_path, label, sem, rate_limit_counter)))

        initial_results = await asyncio.gather(*[t for _, t in chunk_tasks])

        # Check if we hit rate limit abort
        rate_limited_count = sum(1 for r in initial_results if r == _RATE_LIMITED)
        if rate_limited_count > 0:
            successful = sum(1 for r in initial_results if isinstance(r, list) and r)
            logger.error(
                f"Aborted: API rate limit exceeded ({rate_limited_count} batches skipped, "
                f"{successful} batches succeeded before abort)"
            )
            if successful == 0:
                return []

        # Collect results and identify truncated batches for retry
        all_courses_raw: list[dict] = []
        retry_batches: list[list[int]] = []

        for batch_pages, result in zip(batches, initial_results):
            if result == _TRUNCATED:
                retry_batches.append(batch_pages)
            elif isinstance(result, list):
                all_courses_raw.extend(result)

        if retry_batches and rate_limit_counter["consecutive"] < RATE_LIMIT_ABORT_THRESHOLD:
            logger.info(f"Retrying {len(retry_batches)} truncated batches with smaller chunks...")
            retry_tasks = []
            for batch_pages in retry_batches:
                mid = len(batch_pages) // 2
                for sub_pages in [batch_pages[:mid], batch_pages[mid:]]:
                    if not sub_pages:
                        continue
                    chunk_path = _split_pdf_pages(pdf_path, sub_pages, tmp_dir)
                    label = f"pages {sub_pages[0]+1}-{sub_pages[-1]+1} (retry)"
                    retry_tasks.append(_extract_batch(client, chunk_path, label, sem, rate_limit_counter))

            retry_results = await asyncio.gather(*retry_tasks)
            for result in retry_results:
                if isinstance(result, list):
                    all_courses_raw.extend(result)
                elif result == _TRUNCATED:
                    logger.warning("  Retry still truncated — skipping")

    logger.info(f"Total courses extracted (before dedup): {len(all_courses_raw)}")
    unique_courses = _deduplicate_courses(all_courses_raw)
    logger.info(f"After deduplication: {len(unique_courses)} unique courses")

    # Step 5: Cache enriched data (with skill_mappings) directly
    enriched = [_to_enriched_dict(c) for c in unique_courses]

    # Validate skills against taxonomy before caching
    for course in enriched:
        course["skill_mappings"] = [s for s in course.get("skill_mappings", []) if s in UNIFIED_TAXONOMY]

    enriched_cache = CACHE_DIR / f"{college_key}_enriched.json"
    with open(enriched_cache, "w") as f:
        json.dump(enriched, f, indent=2)
    logger.info(f"Cached enriched courses (with skills) to {enriched_cache}")

    # Convert to RawCourse for the pipeline interface
    courses = [_to_raw_course(c) for c in unique_courses]

    # Log stats
    skills_count = sum(1 for c in enriched if c.get("skill_mappings"))
    novel_skills: set[str] = set()
    for c in enriched:
        for s in c.get("skill_mappings", []):
            if s not in UNIFIED_TAXONOMY:
                novel_skills.add(s)

    depts: dict[str, int] = {}
    for c in courses:
        dept = c.department or "Unknown"
        depts[dept] = depts.get(dept, 0) + 1

    logger.info(f"Departments: {len(depts)}")
    for dept, count in sorted(depts.items(), key=lambda x: -x[1])[:10]:
        logger.info(f"  {dept}: {count} courses")
    logger.info(f"Courses with skills: {skills_count}/{len(enriched)}")
    if novel_skills:
        logger.info(f"Novel skills ({len(novel_skills)}): {', '.join(sorted(novel_skills)[:20])}...")

    return courses
