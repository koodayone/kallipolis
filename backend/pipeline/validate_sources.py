"""
Validate catalog PDF sources before running the full pipeline.

Downloads each PDF, checks file size and page count, then spot-checks
a sample of pages with Gemini to confirm course descriptions are present.

Usage:
    python -m pipeline.validate_sources
    python -m pipeline.validate_sources --college foothill
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import httpx
from google import genai
from google.genai import types
from pypdf import PdfReader
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("validate")

CACHE_DIR = Path(__file__).resolve().parent / "cache"
SOURCES_PATH = Path(__file__).resolve().parent / "catalog_sources.json"

# Thresholds
MIN_FILE_SIZE_KB = 500
MIN_PAGE_COUNT = 50

# ── Known catalog platform PDF patterns ───────────────────────────────────────
# When a URL fails validation, probe these patterns to find the real PDF.
# CourseLeaf is the most common platform for CA community college catalogs.
COURSEQULEAF_PDF_PATTERNS = [
    # CourseLeaf full catalog export (most reliable)
    "{base_url}/pdf/",
    # CourseLeaf alternate paths
    "{base_url}/_pdf-books/",
]


async def probe_catalog_pdf_urls(college_key: str) -> list[dict]:
    """
    Probe known catalog platform URL patterns to discover PDF downloads.

    Checks CourseLeaf /pdf/ paths and other known patterns. Returns a list
    of candidate URLs with metadata.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/pdf,*/*",
    }

    # Common catalog base URL patterns for CA community colleges
    base_urls = [
        f"https://catalog.{college_key}college.edu",
        f"https://catalog.{college_key}.edu",
    ]

    candidates = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0, headers=headers) as client:
        for base_url in base_urls:
            for pattern in COURSEQULEAF_PDF_PATTERNS:
                probe_url = pattern.format(base_url=base_url)
                try:
                    resp = await client.get(probe_url)
                    if resp.status_code == 200:
                        text = resp.text
                        # Look for PDF links in the response
                        import re
                        pdf_links = re.findall(r'href="([^"]+\.pdf)"', text)
                        for link in pdf_links:
                            if not link.startswith("http"):
                                full_link = probe_url.rstrip("/") + "/" + link.lstrip("/")
                            else:
                                full_link = link
                            try:
                                head = await client.head(full_link)
                                size = int(head.headers.get("content-length", 0))
                                if size > MIN_FILE_SIZE_KB * 1024:
                                    candidates.append({
                                        "url": full_link,
                                        "size_mb": round(size / (1024 * 1024), 1),
                                        "source": probe_url,
                                    })
                            except Exception:
                                pass
                except Exception:
                    pass

    return candidates


SPOT_CHECK_PROMPT = """Look at these pages from a college course catalog PDF.

Do these pages contain COURSE DESCRIPTIONS — meaning individual courses listed with:
- A course code (e.g., "ENGL 1A", "BUS 010")
- A course title
- A prose description paragraph

Answer with ONLY a JSON object:
{
  "has_course_descriptions": true or false,
  "sample_codes_found": ["CODE1", "CODE2"] (up to 5 course codes you see, or empty array),
  "page_content_type": "brief description of what these pages contain"
}"""


async def download_pdf(url: str, college_key: str) -> Path | None:
    """Download PDF, return path or None on failure."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = CACHE_DIR / f"{college_key}_catalog.pdf"

    if pdf_path.exists():
        logger.info(f"  [{college_key}] Using cached PDF: {pdf_path.name}")
        return pdf_path

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/pdf,*/*",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=120.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "pdf" not in content_type and not response.content[:5] == b"%PDF-":
            logger.error(f"  [{college_key}] Not a PDF (content-type: {content_type})")
            return None

        pdf_path.write_bytes(response.content)
        return pdf_path
    except Exception as e:
        logger.error(f"  [{college_key}] Download failed: {e}")
        return None


def check_size_and_pages(pdf_path: Path, college_key: str) -> tuple[float, int, bool]:
    """Check file size and page count. Returns (size_mb, pages, passed)."""
    size_kb = pdf_path.stat().st_size / 1024
    size_mb = size_kb / 1024

    try:
        reader = PdfReader(pdf_path)
        pages = len(reader.pages)
    except Exception as e:
        logger.error(f"  [{college_key}] Failed to read PDF: {e}")
        return size_mb, 0, False

    passed = size_kb >= MIN_FILE_SIZE_KB and pages >= MIN_PAGE_COUNT

    status = "PASS" if passed else "FAIL"
    logger.info(f"  [{college_key}] {status} — {size_mb:.1f} MB, {pages} pages")

    if not passed:
        if size_kb < MIN_FILE_SIZE_KB:
            logger.warning(f"  [{college_key}] File too small ({size_kb:.0f} KB < {MIN_FILE_SIZE_KB} KB)")
        if pages < MIN_PAGE_COUNT:
            logger.warning(f"  [{college_key}] Too few pages ({pages} < {MIN_PAGE_COUNT})")

    return size_mb, pages, passed


async def spot_check_content(
    client: genai.Client,
    pdf_path: Path,
    college_key: str,
    total_pages: int,
) -> dict:
    """Upload PDF and check a sample of pages for course descriptions."""
    # Pick pages from ~60% through the catalog (where course descriptions typically live)
    sample_start = max(1, int(total_pages * 0.6))
    sample_end = min(sample_start + 5, total_pages)

    try:
        uploaded = client.files.upload(file=pdf_path)

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                uploaded,
                f"Focus on pages {sample_start} through {sample_end}.\n\n{SPOT_CHECK_PROMPT}",
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                temperature=0.1,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

        result = json.loads(response.text.strip())
        has_courses = result.get("has_course_descriptions", False)
        codes = result.get("sample_codes_found", [])
        content_type = result.get("page_content_type", "unknown")

        status = "PASS" if has_courses else "FAIL"
        logger.info(f"  [{college_key}] Content check {status} — {content_type}")
        if codes:
            logger.info(f"  [{college_key}] Sample codes: {', '.join(codes[:5])}")

        return result
    except Exception as e:
        logger.error(f"  [{college_key}] Spot check failed: {e}")
        return {"has_course_descriptions": None, "error": str(e)}


async def validate_college(
    college_key: str,
    info: dict,
    gemini_client: genai.Client,
    sem: asyncio.Semaphore,
) -> dict:
    """Validate a single college's catalog PDF."""
    url = info["catalog_pdf_url"]
    result = {
        "college": college_key,
        "name": info["name"],
        "url": url,
        "download": False,
        "size_mb": 0,
        "pages": 0,
        "size_check": False,
        "has_course_descriptions": None,
        "overall": "FAIL",
    }

    # Step 1: Download
    pdf_path = await download_pdf(url, college_key)
    if not pdf_path:
        # Auto-probe known platform patterns before giving up
        candidates = await probe_catalog_pdf_urls(college_key)
        if candidates:
            logger.info(f"  [{college_key}] Auto-discovered {len(candidates)} candidate PDFs:")
            for c in candidates:
                logger.info(f"    {c['size_mb']}MB — {c['url']}")
            result["suggested_urls"] = candidates
        return result
    result["download"] = True

    # Step 2: Size & page check
    size_mb, pages, size_ok = check_size_and_pages(pdf_path, college_key)
    result["size_mb"] = round(size_mb, 1)
    result["pages"] = pages
    result["size_check"] = size_ok

    if not size_ok:
        # PDF downloaded but too small — probe for the real one
        candidates = await probe_catalog_pdf_urls(college_key)
        if candidates:
            logger.info(f"  [{college_key}] PDF too small. Auto-discovered {len(candidates)} candidate PDFs:")
            for c in candidates:
                logger.info(f"    {c['size_mb']}MB — {c['url']}")
            result["suggested_urls"] = candidates
        return result

    # Step 3: Content spot-check
    async with sem:
        spot = await spot_check_content(gemini_client, pdf_path, college_key, pages)
    result["has_course_descriptions"] = spot.get("has_course_descriptions")
    result["content_type"] = spot.get("page_content_type", "")
    result["sample_codes"] = spot.get("sample_codes_found", [])

    if result["has_course_descriptions"]:
        result["overall"] = "PASS"

    return result


async def validate_all(college_filter: str | None = None):
    """Validate all (or one) college catalog sources."""
    with open(SOURCES_PATH) as f:
        data = json.load(f)

    colleges = {
        k: v for k, v in data["colleges"].items()
        if v.get("catalog_pdf_url")
        and (college_filter is None or k == college_filter)
    }

    if not colleges:
        logger.error("No colleges to validate.")
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")

    client = genai.Client(api_key=api_key)
    sem = asyncio.Semaphore(3)  # limit concurrent Gemini calls

    logger.info(f"Validating {len(colleges)} college catalog PDFs...\n")

    tasks = [
        validate_college(key, info, client, sem)
        for key, info in colleges.items()
    ]
    results = await asyncio.gather(*tasks)

    # Summary
    passed = [r for r in results if r["overall"] == "PASS"]
    failed = [r for r in results if r["overall"] == "FAIL"]

    print("\n" + "=" * 70)
    print(f"VALIDATION SUMMARY: {len(passed)}/{len(results)} passed")
    print("=" * 70)

    for r in sorted(results, key=lambda x: x["college"]):
        icon = "PASS" if r["overall"] == "PASS" else "FAIL"
        desc = f'{r["size_mb"]}MB, {r["pages"]}pg'
        if r.get("content_type"):
            desc += f' — {r["content_type"][:50]}'
        print(f"  [{icon}] {r['college']:15s} {r['name']:40s} {desc}")

    if failed:
        print(f"\nFailed colleges ({len(failed)}):")
        for r in failed:
            reasons = []
            if not r["download"]:
                reasons.append("download failed")
            elif not r["size_check"]:
                reasons.append(f"too small ({r['size_mb']}MB, {r['pages']}pg)")
            elif not r["has_course_descriptions"]:
                reasons.append("no course descriptions found in sample")
            print(f"  {r['college']:15s} — {', '.join(reasons)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate catalog PDF sources")
    parser.add_argument("--college", help="Validate a single college")
    args = parser.parse_args()

    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(env_path)

    asyncio.run(validate_all(college_filter=args.college))


if __name__ == "__main__":
    main()
