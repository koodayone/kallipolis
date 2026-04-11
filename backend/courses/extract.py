"""
MCF-guided course extraction + skill derivation pipeline.

Pre-extracts text with pypdf, filters to course pages, sends text to
Gemini Flash for structured extraction + skill assignment from the
unified taxonomy (closed vocabulary).

Usage:
    python -m pipeline.extract --college foothill
    python -m pipeline.extract --all
    python -m pipeline.extract --college foothill --force
    python -m pipeline.extract --mcf-only
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types
from pypdf import PdfReader

from pipeline.mcf_key_map import pdf_to_mcf_key

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent.parent / "pipeline" / "cache"
MCF_DIR = Path("/Users/dayonekoo/Desktop/cc_dataset/mastercoursefiles")
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "pipeline" / "extraction_prompt.txt"

# ── Constants ──────────────────────────────────────────────────────────────

PAGES_PER_CHUNK = 10
MAX_CHARS_PER_CHUNK = 30000
MAX_RETRIES = 5
CONCURRENCY = 10
COURSE_CODE_RE = re.compile(r"\b[A-Z][A-Z .]{1,8}\s*\d{1,4}[A-Z]{0,2}\b")
COURSE_KEYWORDS = {"units", "hours", "prerequisite", "advisory", "transfer credit",
                   "corequisite", "lecture", "lab", "grading"}


# ── MCF Parsing ────────────────────────────────────────────────────────────

def _normalize_course_id(raw_id: str) -> str:
    """Normalize MCF 12-char fixed-width Course ID to catalog format."""
    cleaned = raw_id.rstrip(". ")
    if re.search(r"[A-Z]\s+\d", cleaned):
        return cleaned
    match = re.match(r"^([A-Z ]+?)(\d.*)$", cleaned)
    if match:
        return f"{match.group(1).rstrip()} {match.group(2)}"
    return cleaned


def _parse_mcf(mcf_path: Path) -> dict[str, dict]:
    """Parse MCF CSV -> {normalized_code: {top_code, top4, max_units, ...}}."""
    if not mcf_path.exists():
        return {}
    courses: dict[str, dict] = {}
    with open(mcf_path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 7:
                continue
            normalized = _normalize_course_id(row[2])
            if not normalized:
                continue
            top6 = row[3].strip()
            courses[normalized] = {
                "top_code": top6,
                "top4": top6[:4] if len(top6) >= 4 else "",
                "max_units": row[5].strip(),
                "min_units": row[6].strip(),
                "credit_status": row[4].strip(),
            }
    return courses


def _load_mcf(college_key: str) -> dict[str, dict]:
    """Load MCF for a college, handling key mapping."""
    mcf_key = pdf_to_mcf_key(college_key)
    for key in [mcf_key, college_key]:
        path = MCF_DIR / f"MasterCourseFile_{key}.csv"
        if path.exists():
            data = _parse_mcf(path)
            if data:
                logger.info(f"  MCF: {len(data)} courses from {path.name}")
                return data
    logger.warning(f"  MCF: not found for {college_key}")
    return {}


# ── PDF Text Pre-extraction ───────────────────────────────────────────────

def _is_course_page(text: str) -> bool:
    """Check if a page likely contains course descriptions."""
    if len(text) < 200:
        return False
    codes = COURSE_CODE_RE.findall(text)
    if len(codes) < 2:
        return False
    text_lower = text.lower()
    keyword_hits = sum(1 for kw in COURSE_KEYWORDS if kw in text_lower)
    return keyword_hits >= 2


def preprocess_college(pdf_path: Path) -> tuple[list[dict], int]:
    """Extract text from course-bearing pages. Returns (pages, total_pages)."""
    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    pages = []
    for i in range(total):
        text = reader.pages[i].extract_text() or ""
        if _is_course_page(text):
            pages.append({"page": i + 1, "text": text})
    return pages, total


def _chunk_pages(pages: list[dict]) -> list[list[dict]]:
    """Group pages into chunks by character budget."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0
    for p in pages:
        text_len = len(p["text"])
        if current and (current_chars + text_len > MAX_CHARS_PER_CHUNK or len(current) >= PAGES_PER_CHUNK):
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(p)
        current_chars += text_len
    if current:
        chunks.append(current)
    return chunks


# ── Gemini Flash Extraction ───────────────────────────────────────────────

def _build_chunk_prompt(chunk: list[dict], mcf_codes: list[str] | None = None) -> str:
    """Build prompt with extracted text inline."""
    page_nums = [p["page"] for p in chunk]
    page_range = f"{page_nums[0]}-{page_nums[-1]}"

    prompt = (
        f"Below is text from pages {page_range} of a California community college catalog. "
        f"Extract every course and assign skill mappings.\n\n"
    )
    if mcf_codes:
        prompt += f"Expected course codes (partial): {', '.join(mcf_codes[:60])}\n\n"
    prompt += (
        "Return a JSON array. Fields: code, name, department, units, description, "
        "prerequisites, learning_outcomes, course_objectives, transfer_status, "
        "ge_area, grading, hours, skill_mappings (at least 6 skills per course).\n\n"
        "--- CATALOG TEXT ---\n\n"
    )
    for p in chunk:
        prompt += f"[Page {p['page']}]\n{p['text']}\n\n"
    return prompt


async def _extract_chunk(
    client: genai.Client,
    chunk: list[dict],
    mcf_codes: list[str] | None,
    sem: asyncio.Semaphore,
    system_instruction: str,
) -> list[dict]:
    """Extract courses from a single chunk via Gemini Flash."""
    prompt = _build_chunk_prompt(chunk, mcf_codes)

    for attempt in range(MAX_RETRIES):
        async with sem:
            try:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=65536,
                        temperature=0.2,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=0,
                        ),
                    ),
                )

                text = response.text.strip()
                courses = json.loads(text)
                if isinstance(courses, list):
                    return [c for c in courses if isinstance(c, dict) and c.get("code")]
                else:
                    logger.warning(f"    Unexpected format: {text[:200]}")
                    return []

            except json.JSONDecodeError as e:
                logger.warning(f"    JSON parse error: {e}")
                return []
            except Exception as e:
                error_str = str(e).lower()
                if "resource_exhausted" in error_str or "429" in error_str:
                    wait = 2 ** attempt * 5
                    logger.info(f"    Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"    Gemini error: {e}")
                    return []

    logger.error("    Exhausted retries")
    return []


async def _extract_all_chunks(
    chunks: list[list[dict]],
    mcf_codes: list[str] | None,
) -> list[tuple[int, list[dict]]]:
    """Extract all chunks concurrently via Gemini Flash."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")

    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)
    system_instruction = SYSTEM_PROMPT_PATH.read_text()

    tasks = [
        _extract_chunk(client, chunk, mcf_codes, sem, system_instruction)
        for chunk in chunks
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    indexed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"  Chunk {i+1} exception: {result}")
            indexed.append((i, []))
        else:
            indexed.append((i, result))
    return indexed


# ── Post-processing ────────────────────────────────────────────────────────

def _deduplicate_courses(all_courses: list[dict]) -> list[dict]:
    """Deduplicate by course code, keeping most populated entry."""
    seen: dict[str, dict] = {}
    for course in all_courses:
        code = course.get("code", "").strip()
        if not code:
            continue
        if code not in seen:
            seen[code] = course
        else:
            if sum(1 for v in course.values() if v) > sum(1 for v in seen[code].values() if v):
                seen[code] = course
    return list(seen.values())


def _validate_skills(courses: list[dict]) -> list[dict]:
    """Validate skills against UNIFIED_TAXONOMY. Drop off-taxonomy terms."""
    from ontology.skills import UNIFIED_TAXONOMY
    off_taxonomy: Counter = Counter()
    for course in courses:
        skills = course.get("skill_mappings", [])
        valid = []
        seen = set()
        for s in skills:
            s = s.strip()
            if s in UNIFIED_TAXONOMY and s not in seen:
                valid.append(s)
                seen.add(s)
            elif s not in UNIFIED_TAXONOMY:
                off_taxonomy[s] += 1
        course["skill_mappings"] = valid
    if off_taxonomy:
        logger.warning(f"  Off-taxonomy skills dropped: {len(off_taxonomy)} unique terms")
        for term, count in off_taxonomy.most_common(5):
            logger.warning(f"    '{term}': {count} occurrences")
    return courses


def _cross_reference_mcf(courses: list[dict], mcf_data: dict[str, dict]) -> list[dict]:
    """Add top_code from MCF."""
    matched = 0
    for course in courses:
        code = course.get("code", "").strip()
        entry = mcf_data.get(code) or mcf_data.get(re.sub(r"\s+", " ", code).strip())
        if entry:
            course["top_code"] = entry["top_code"]
            course["top4"] = entry["top4"]
            if not course.get("units") and entry.get("max_units"):
                course["units"] = entry["max_units"]
            matched += 1
    logger.info(f"  MCF cross-reference: {matched}/{len(courses)} matched")
    return courses


# ── Coverage Reporting ─────────────────────────────────────────────────────

def _write_coverage(college_key, courses, mcf_data, total_pages, course_pages, failed):
    from ontology.skills import UNIFIED_TAXONOMY
    all_skills = [s for c in courses for s in c.get("skill_mappings", [])]
    unique = set(all_skills)
    report = {
        "college": college_key,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pdf_pages_total": total_pages,
        "pdf_pages_with_courses": course_pages,
        "chunks_failed": failed,
        "courses_extracted": len(courses),
        "courses_with_skills": sum(1 for c in courses if c.get("skill_mappings")),
        "avg_skills_per_course": round(len(all_skills) / max(len(courses), 1), 1),
        "mcf_matched": sum(1 for c in courses if c.get("top_code")),
        "unique_skills": len(unique),
        "taxonomy_skills": len(unique & UNIFIED_TAXONOMY),
        "off_taxonomy_skills": len(unique - UNIFIED_TAXONOMY),
    }
    path = CACHE_DIR / f"{college_key}_coverage.json"
    path.write_text(json.dumps(report, indent=2))
    logger.info(f"  Coverage: {report['courses_extracted']} courses, "
                f"{report['taxonomy_skills']} taxonomy / {report['off_taxonomy_skills']} off-taxonomy skills")


# ── MCF-Only Fallback ──────────────────────────────────────────────────────

def _extract_mcf_only(college_key: str) -> list[dict]:
    mcf_data = _load_mcf(college_key)
    if not mcf_data:
        return []
    courses = []
    for code, info in mcf_data.items():
        prefix_match = re.match(r"^([A-Z ]+)", code)
        courses.append({
            "code": code, "name": "", "department": (prefix_match.group(1).strip() if prefix_match else ""),
            "units": info.get("max_units", ""), "description": "", "prerequisites": "",
            "learning_outcomes": [], "course_objectives": [], "transfer_status": "",
            "ge_area": "", "grading": "", "hours": "", "skill_mappings": [],
            "top_code": info.get("top_code", ""), "top4": info.get("top4", ""),
        })
    path = CACHE_DIR / f"{college_key}_enriched.json"
    path.write_text(json.dumps(courses, indent=2))
    logger.warning(f"  MCF-only: {len(courses)} courses (no descriptions/skills)")
    return courses


# ── Main Orchestration ─────────────────────────────────────────────────────

def extract_college(college_key: str, force: bool = False) -> list[dict] | None:
    logger.info(f"{'=' * 60}")
    logger.info(f"Extracting: {college_key}")

    enriched_path = CACHE_DIR / f"{college_key}_enriched.json"
    if enriched_path.exists() and not force:
        try:
            existing = json.loads(enriched_path.read_text())
            with_skills = sum(1 for c in existing if c.get("skill_mappings"))
            if with_skills > 10:
                logger.info(f"  Skipping — {len(existing)} courses cached. Use --force.")
                return None
        except (json.JSONDecodeError, KeyError):
            pass

    pdf_path = CACHE_DIR / f"{college_key}_catalog.pdf"
    if not pdf_path.exists():
        logger.warning(f"  No PDF — MCF-only fallback")
        return _extract_mcf_only(college_key)

    mcf_data = _load_mcf(college_key)
    mcf_codes = sorted(mcf_data.keys()) if mcf_data else None

    # Phase 0: Pre-extract text
    course_pages, total_pages = preprocess_college(pdf_path)
    logger.info(f"  PDF: {total_pages} pages, {len(course_pages)} with course content")

    if not course_pages:
        logger.warning(f"  No course pages detected — MCF-only fallback")
        return _extract_mcf_only(college_key)

    chunks = _chunk_pages(course_pages)
    logger.info(f"  Chunks: {len(chunks)} (max {PAGES_PER_CHUNK} pages / {MAX_CHARS_PER_CHUNK//1000}K chars each)")

    # Phase 1: Async parallel extraction via Gemini Flash
    indexed_results = asyncio.run(_extract_all_chunks(chunks, mcf_codes))

    all_courses: list[dict] = []
    failed = 0

    for idx, courses in indexed_results:
        chunk = chunks[idx]
        page_range = f"{chunk[0]['page']}-{chunk[-1]['page']}"
        if courses:
            all_courses.extend(courses)
            logger.info(f"  Chunk {idx+1}/{len(chunks)} (pp {page_range}): {len(courses)} courses")
        else:
            failed += 1
            logger.warning(f"  Chunk {idx+1}/{len(chunks)} (pp {page_range}): 0 courses")

    if not all_courses:
        logger.error(f"  No courses extracted")
        return None

    # Phase 2: Post-processing
    unique = _deduplicate_courses(all_courses)
    logger.info(f"  Dedup: {len(all_courses)} raw -> {len(unique)} unique")

    unique = _validate_skills(unique)

    if mcf_data:
        unique = _cross_reference_mcf(unique, mcf_data)

    enriched_path.write_text(json.dumps(unique, indent=2))
    logger.info(f"  Wrote {len(unique)} courses to {enriched_path.name}")

    _write_coverage(college_key, unique, mcf_data, total_pages, len(course_pages), failed)
    return unique


def extract_all(force: bool = False) -> None:
    pdfs = sorted(CACHE_DIR.glob("*_catalog.pdf"))
    keys = [p.stem.replace("_catalog", "") for p in pdfs]
    logger.info(f"Found {len(keys)} college PDFs")

    results = {"success": [], "skipped": [], "failed": []}
    for key in keys:
        try:
            result = extract_college(key, force=force)
            if result is None:
                results["skipped"].append(key)
            else:
                results["success"].append(key)
        except Exception as e:
            logger.error(f"  EXCEPTION for {key}: {e}")
            results["failed"].append(key)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"DONE: {len(results['success'])} extracted, "
                f"{len(results['skipped'])} skipped, {len(results['failed'])} failed")
    if results["failed"]:
        logger.info(f"Failed: {', '.join(results['failed'])}")


def extract_mcf_only_all() -> None:
    mcf_files = sorted(MCF_DIR.glob("MasterCourseFile_*.csv"))
    pdf_keys = {p.stem.replace("_catalog", "") for p in CACHE_DIR.glob("*_catalog.pdf")}
    from pipeline.mcf_key_map import mcf_to_pdf_key
    for f in mcf_files:
        mcf_key = f.stem.replace("MasterCourseFile_", "")
        pdf_key = mcf_to_pdf_key(mcf_key)
        if pdf_key not in pdf_keys and mcf_key not in pdf_keys:
            _extract_mcf_only(pdf_key)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MCF-guided course extraction via Gemini Flash")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--college", type=str)
    group.add_argument("--all", action="store_true")
    group.add_argument("--mcf-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")

    if args.mcf_only:
        extract_mcf_only_all()
    elif getattr(args, "all"):
        extract_all(force=args.force)
    else:
        extract_college(args.college, force=args.force)


if __name__ == "__main__":
    main()
