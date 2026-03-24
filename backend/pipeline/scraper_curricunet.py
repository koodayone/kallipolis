"""
CurricUNET (Acadea) course outline scraper.

Scrapes Course Outlines of Record from colleges using the CurricUNET
curriculum management platform. ~73 California Community Colleges use
this system and expose public CORs at {college}.curriqunet.com.

Output is a list[RawCourse] — same contract as the CourseLeaf scraper.

Usage:
    from pipeline.scraper_curricunet import scrape_curricunet
    courses = await scrape_curricunet("https://ccsf.curriqunet.com", report_id=28)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from html.parser import HTMLParser
from pathlib import Path

import httpx

from pipeline.scraper import RawCourse

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CONCURRENCY = 10
DELAY = 0.15  # seconds between course page fetches

SCAN_CONCURRENCY = 30
SCAN_DELAY = 0.02  # lighter delay for enumeration probes

COMMON_REPORT_IDS = [28, 99, 48, 52, 44]

CACHE_DIR = Path(__file__).resolve().parent / "cache"

# ── URL helpers ───────────────────────────────────────────────────────────────


def _build_course_url(base_url: str, entity_id: int, report_id: int) -> str:
    return (
        f"{base_url}/DynamicReports/AllFieldsReportByEntity/"
        f"{entity_id}?entityType=Course&reportId={report_id}"
    )


# ── HTTP fetch (adapted for CurricUNET's 500 = not found pattern) ────────────


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch a URL. Returns HTML on success, None on 404/500/error."""
    for attempt in range(3):
        try:
            resp = await client.get(url, timeout=30.0)
            if resp.status_code == 200:
                return resp.text
            # CurricUNET returns 500 for invalid entity IDs (not 404)
            if resp.status_code in (404, 500):
                return None
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
        except httpx.RequestError as e:
            if attempt < 2:
                await asyncio.sleep(1)
            else:
                logger.warning(f"Request error for {url}: {e}")
    return None


# ── reportId discovery ────────────────────────────────────────────────────────


async def _discover_report_id(
    client: httpx.AsyncClient,
    base_url: str,
) -> int | None:
    """Try common reportIds against a few entity IDs to find one that works."""
    # Try a few low entity IDs that are likely to exist
    probe_ids = [1, 2, 5, 10, 50, 100]

    for report_id in COMMON_REPORT_IDS:
        for entity_id in probe_ids:
            url = _build_course_url(base_url, entity_id, report_id)
            html = await _fetch(client, url)
            if html and "report-entity-title" in html:
                logger.info(f"Discovered reportId={report_id} via entity {entity_id}")
                return report_id
    return None


# ── Course enumeration ────────────────────────────────────────────────────────


async def _probe_entity(
    client: httpx.AsyncClient,
    url: str,
    sem: asyncio.Semaphore,
) -> bool:
    """Check if an entity ID returns a valid course page using HEAD request."""
    async with sem:
        await asyncio.sleep(SCAN_DELAY)
        try:
            resp = await client.head(url, timeout=10.0)
            # Valid courses return 200 with substantial content;
            # invalid ones return 500 with ~276 bytes
            if resp.status_code != 200:
                return False
            content_length = int(resp.headers.get("content-length", "0"))
            return content_length > 500
        except (httpx.RequestError, ValueError):
            return False


async def _find_max_entity_id(
    client: httpx.AsyncClient,
    base_url: str,
    report_id: int,
) -> int:
    """Binary search to find the approximate upper bound of entity IDs."""
    # Exponential probe to find a ceiling
    ceiling = 1000
    while ceiling <= 100_000:
        url = _build_course_url(base_url, ceiling, report_id)
        html = await _fetch(client, url)
        if html is None or "report-entity-title" not in html:
            # Check a few IDs above to make sure we're really past the end
            found_above = False
            for offset in [100, 500, 1000]:
                check_url = _build_course_url(base_url, ceiling + offset, report_id)
                check_html = await _fetch(client, check_url)
                if check_html and "report-entity-title" in check_html:
                    found_above = True
                    ceiling = ceiling + offset
                    break
            if not found_above:
                break
        ceiling *= 2

    # Binary search between ceiling/2 and ceiling
    lo, hi = ceiling // 2, ceiling
    while lo < hi - 100:
        mid = (lo + hi) // 2
        # Check a small range around mid
        found = False
        for offset in range(0, 50, 10):
            url = _build_course_url(base_url, mid + offset, report_id)
            html = await _fetch(client, url)
            if html and "report-entity-title" in html:
                found = True
                break
        if found:
            lo = mid
        else:
            hi = mid

    # Add buffer for safety
    max_id = hi + 500
    logger.info(f"Estimated max entity ID: ~{max_id}")
    return max_id


async def _enumerate_courses(
    client: httpx.AsyncClient,
    base_url: str,
    report_id: int,
    college_key: str | None = None,
) -> list[int]:
    """Find all valid course entity IDs by scanning the ID range."""
    # Check cache first
    if college_key:
        cache_path = CACHE_DIR / f"{college_key}_entity_ids.json"
        if cache_path.exists():
            entity_ids = json.loads(cache_path.read_text())
            logger.info(f"Loaded {len(entity_ids)} cached entity IDs from {cache_path}")
            return entity_ids

    max_id = await _find_max_entity_id(client, base_url, report_id)

    # Scan all IDs concurrently
    sem = asyncio.Semaphore(SCAN_CONCURRENCY)
    valid_ids: list[int] = []
    batch_size = 500

    for batch_start in range(1, max_id + 1, batch_size):
        batch_end = min(batch_start + batch_size, max_id + 1)
        tasks = []
        ids_in_batch = list(range(batch_start, batch_end))

        for eid in ids_in_batch:
            url = _build_course_url(base_url, eid, report_id)
            tasks.append(_probe_entity(client, url, sem))

        results = await asyncio.gather(*tasks)
        for eid, is_valid in zip(ids_in_batch, results):
            if is_valid:
                valid_ids.append(eid)

        if batch_start % 2000 < batch_size:
            logger.info(
                f"Scanned {batch_end - 1}/{max_id} IDs, "
                f"found {len(valid_ids)} valid courses so far"
            )

    logger.info(f"Enumeration complete: {len(valid_ids)} valid course IDs in range 1-{max_id}")

    # Cache results
    if college_key:
        cache_path = CACHE_DIR / f"{college_key}_entity_ids.json"
        cache_path.write_text(json.dumps(valid_ids))
        logger.info(f"Cached entity IDs to {cache_path}")

    return valid_ids


# ── HTML Parser ───────────────────────────────────────────────────────────────


class CurricUNETCourseParser(HTMLParser):
    """Parses a CurricUNET DynamicReports course outline into a RawCourse."""

    def __init__(self):
        super().__init__()
        self.course = RawCourse()

        # Section tracking (from .h3 div text)
        self._current_section: str | None = None
        self._in_section_header = False
        self._section_header_text = ""

        # Field label/value tracking
        self._in_label = False
        self._label_text = ""
        self._in_value = False
        self._value_depth = 0
        self._value_text = ""

        # Title tracking
        self._in_title = False
        self._title_text = ""

        # SLO list item tracking
        self._in_li = False
        self._li_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_dict = dict(attrs)
        cls = attr_dict.get("class", "")

        # Section header: <div class="h3">SECTION NAME</div>
        if tag == "div" and cls == "h3":
            self._in_section_header = True
            self._section_header_text = ""

        # Course title: <h3 class="report-entity-title ...">
        if tag == "h3" and "report-entity-title" in cls:
            self._in_title = True
            self._title_text = ""

        # Field label: <label class="... field-label">
        if tag == "label" and "field-label" in cls:
            self._in_label = True
            self._label_text = ""

        # Field value: <span class="... field-value">
        if tag == "span" and "field-value" in cls:
            self._in_value = True
            self._value_depth = 1
            self._value_text = ""

        # Track nested tags inside value spans
        if self._in_value and tag != "span":
            if tag == "br":
                self._value_text += "\n"
            elif tag == "li":
                self._in_li = True
                self._li_text = ""
            self._value_depth += 1 if tag in ("span", "div", "ol", "ul") else 0

        # Standalone <li> inside value
        if tag == "li" and self._in_value:
            self._in_li = True
            self._li_text = ""

    def handle_endtag(self, tag: str):
        # Section header end
        if tag == "div" and self._in_section_header:
            self._in_section_header = False
            header = self._section_header_text.strip().upper()
            if "GENERAL DESCRIPTION" in header:
                self._current_section = "general"
            elif "CATALOG DESCRIPTION" in header:
                self._current_section = "description"
            elif "STUDENT LEARNING OUTCOME" in header:
                self._current_section = "slo"
            elif "COURSE OBJECTIVE" in header:
                self._current_section = "objectives"
            elif "CONTENT" in header:
                self._current_section = "contents"  # topic outline, not objectives
            elif "COURSE SPECIFICS" in header:
                self._current_section = "specifics"
            elif "INSTRUCTIONAL METHODOLOGY" in header:
                self._current_section = "methodology"
            else:
                self._current_section = header.lower()

        # Title end
        if tag == "h3" and self._in_title:
            self._in_title = False
            self._parse_title(self._title_text.strip())

        # Field label end
        if tag == "label" and self._in_label:
            self._in_label = False

        # List item end — collect SLO or objective
        if tag == "li" and self._in_li and self._in_value:
            self._in_li = False
            item = self._li_text.strip()
            if item:
                if self._current_section == "slo":
                    self.course.learning_outcomes.append(item)
                elif self._current_section == "objectives":
                    self.course.course_objectives.append(item)

        # Field value end
        if tag == "span" and self._in_value:
            self._in_value = False
            self._assign_field()

    def handle_data(self, data: str):
        if self._in_section_header:
            self._section_header_text += data
        if self._in_title:
            self._title_text += data
        if self._in_label:
            self._label_text += data
        if self._in_value:
            self._value_text += data
            if self._in_li:
                self._li_text += data

    def _parse_title(self, text: str):
        """Parse 'CODE - Name' from report-entity-title."""
        # Handle formats like "CDEV 67 - Child, Family, and Community"
        match = re.match(r"^([A-Z]+\s*\d+[A-Z]?(?:\.\d+)?)\s*[-–—]\s*(.+)$", text)
        if match:
            self.course.code = match.group(1).strip()
            self.course.name = match.group(2).strip()
            # Derive department from code prefix
            dept_match = re.match(r"^([A-Z]+)", self.course.code)
            if dept_match:
                self.course.department = dept_match.group(1)

    def _assign_field(self):
        """Assign the accumulated label/value to the correct RawCourse field."""
        label = self._label_text.strip().lower()
        value = self._value_text.strip()

        if not label or not value:
            # Unlabeled value in description section = the description itself
            if self._current_section == "description" and value:
                self.course.description = value
            return

        # General description fields
        if self._current_section == "general":
            if label == "department":
                # Full department name from COR (overrides code-derived acronym)
                # Must be exact match — "department chairperson" is a different field
                self.course.department = value
            elif "course number" in label:
                self.course.code = value
            elif "course title" in label:
                self.course.name = value

        # Course specifics
        elif self._current_section == "specifics":
            if label.startswith("unit"):
                # Some records have "Units: 3" as the value; strip the prefix
                self.course.units = re.sub(r"^units:\s*", "", value, flags=re.IGNORECASE)
            elif label.startswith("hour"):
                self.course.hours = value
            elif "requisite" in label:
                self.course.prerequisites = value
            elif "transfer" in label:
                self.course.transfer_status = value
            elif "general education" in label or label.startswith("ge"):
                self.course.ge_area = value
            elif "grading" in label or "method of grading" in label:
                self.course.grading = value

        # Catalog description (unlabeled value handled above)
        elif self._current_section == "description":
            if not self.course.description:
                self.course.description = value

        # SLO section — list items handled in handle_endtag
        # But some SLOs are in a single value field without <li> tags
        elif self._current_section == "slo":
            if "upon completion" in label:
                # The label is the header; value contains the SLO list
                # If no <li> tags were found, split by newlines
                if not self.course.learning_outcomes and value:
                    lines = [ln.strip() for ln in value.split("\n") if ln.strip()]
                    self.course.learning_outcomes.extend(lines)

        # Reset label for next field
        self._label_text = ""
        self._value_text = ""


# ── Page parsing ──────────────────────────────────────────────────────────────


async def _parse_course_page(
    client: httpx.AsyncClient,
    base_url: str,
    entity_id: int,
    report_id: int,
    sem: asyncio.Semaphore,
) -> RawCourse | None:
    """Fetch and parse a single CurricUNET course outline."""
    async with sem:
        await asyncio.sleep(DELAY)
        url = _build_course_url(base_url, entity_id, report_id)
        html = await _fetch(client, url)

    if not html:
        return None

    # Skip non-course records (modifications, deactivations, etc.)
    # These have titles like "A2. Credit Course (Degree-Applicable) - Modification: ..."
    if re.search(r"- (Modification|Deactivation|Reactivation):", html[:2000]):
        return None

    parser = CurricUNETCourseParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.warning(f"Parse error for entity {entity_id}: {e}")
        return None

    course = parser.course
    course.url = _build_course_url(base_url, entity_id, report_id)

    # Validate: must have at least a code and name
    if not course.code or not course.name:
        return None

    return course


# ── Main entry point ──────────────────────────────────────────────────────────


async def scrape_curricunet(
    base_url: str,
    report_id: int | None = None,
    college_key: str | None = None,
) -> list[RawCourse]:
    """
    Scrape all course outlines from a CurricUNET instance.

    Args:
        base_url: Base URL, e.g., "https://ccsf.curriqunet.com"
        report_id: The reportId for course outlines. Auto-discovered if None.
        college_key: Optional key for caching entity IDs.

    Returns:
        List of RawCourse objects with populated COR fields.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "Kallipolis/1.0"},
        follow_redirects=True,
    ) as client:

        # Step 1: Discover reportId if not provided
        if report_id is None:
            logger.info("Discovering reportId...")
            report_id = await _discover_report_id(client, base_url)
            if report_id is None:
                logger.error("Could not discover a valid reportId")
                return []
            logger.info(f"Using reportId={report_id}")

        # Step 2: Enumerate all valid course entity IDs
        logger.info("Enumerating course entity IDs...")
        entity_ids = await _enumerate_courses(client, base_url, report_id, college_key)
        if not entity_ids:
            logger.error("No valid course entity IDs found")
            return []

        # Step 3: Fetch and parse all course pages
        logger.info(f"Fetching {len(entity_ids)} course outlines...")
        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [
            _parse_course_page(client, base_url, eid, report_id, sem)
            for eid in entity_ids
        ]
        results = await asyncio.gather(*tasks)

        courses = [c for c in results if c is not None]

        # Deduplicate by course code (keep the first/latest version)
        seen_codes: set[str] = set()
        unique_courses: list[RawCourse] = []
        for course in courses:
            if course.code not in seen_codes:
                seen_codes.add(course.code)
                unique_courses.append(course)

        logger.info(
            f"Successfully parsed {len(unique_courses)} unique courses "
            f"(from {len(courses)} total records)"
        )
        return unique_courses
