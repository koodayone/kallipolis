"""
Stage 1: CourseLeaf catalog scraper.

Scrapes a CourseLeaf-based college catalog to extract full Course Outline
of Record (COR) data for every course.

Usage:
    from courses.scrape import scrape_catalog
    courses = await scrape_catalog("https://catalog.foothill.edu")
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

# ── Data structures ────────────────────────────────────────────────────────────


@dataclass
class RawCourse:
    """Raw course data extracted from a CourseLeaf catalog page."""

    name: str = ""
    code: str = ""
    department: str = ""
    units: str = ""
    description: str = ""
    prerequisites: str = ""
    learning_outcomes: list[str] = field(default_factory=list)
    course_objectives: list[str] = field(default_factory=list)
    transfer_status: str = ""
    ge_area: str = ""
    grading: str = ""
    hours: str = ""
    url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── HTML Parsers ───────────────────────────────────────────────────────────────


class CourseOutlineIndexParser(HTMLParser):
    """Parses /course-outlines/ to extract all course outline links."""

    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            # Match links like /course-outlines/ACTG-1A/ but not .pdf files
            if href.startswith("/course-outlines/") and not href.endswith(".pdf"):
                # Avoid the index page itself
                if href.rstrip("/") != "/course-outlines":
                    self.links.append(href)


class CourseOutlineParser(HTMLParser):
    """Parses a course outline page to extract COR fields."""

    def __init__(self):
        super().__init__()
        self.course = RawCourse()

        self._current_section: str | None = None
        self._in_li = False
        self._li_buffer = ""
        self._h1_count = 0
        self._in_h1 = False
        self._h1_text = ""
        self._found_title = False
        self._in_h2 = False
        self._h2_text = ""
        self._section_items: list[str] = []
        self._in_cor_table = False
        self._in_td = False
        self._current_td_text = ""
        self._tr_cells: list[str] = []
        self._in_desc_section = False
        self._in_desc_div = False
        self._desc_buffer = ""
        self._desc_div_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "h1":
            self._h1_count += 1
            # Prefer h1 with class "page-title" (Citrus-style),
            # otherwise fall back to the second h1 (Foothill-style)
            if "page-title" in cls or self._h1_count == 2:
                if not self._found_title:
                    self._in_h1 = True
                    self._h1_text = ""

        if tag == "h2":
            self._flush_section()
            self._in_h2 = True
            self._h2_text = ""

        if tag == "table" and "sc_cor" in cls:
            self._in_cor_table = True

        if self._in_cor_table and tag == "td":
            self._in_td = True
            self._current_td_text = ""

        if self._in_cor_table and tag == "tr":
            self._tr_cells = []

        if tag == "li" and self._current_section in ("slo", "objectives"):
            self._in_li = True
            self._li_buffer = ""

        # Capture description: it's a <div> after the "Description" h2
        if self._in_desc_section and tag == "div" and not self._in_desc_div:
            self._in_desc_div = True
            self._desc_buffer = ""
            self._desc_div_depth = 1
        elif self._in_desc_div and tag == "div":
            self._desc_div_depth += 1

    def handle_endtag(self, tag):
        if tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._found_title = True
            self._parse_h1(self._h1_text.strip())

        if tag == "h2" and self._in_h2:
            self._in_h2 = False
            section = self._h2_text.strip().lower()
            if "student learning outcome" in section:
                self._current_section = "slo"
            elif "course objective" in section:
                self._current_section = "objectives"
            elif "description" in section:
                self._current_section = "description"
                self._in_desc_section = True
            else:
                self._current_section = section

        if self._in_cor_table and tag == "td":
            self._in_td = False
            self._tr_cells.append(self._current_td_text.strip())

        if self._in_cor_table and tag == "tr":
            if len(self._tr_cells) >= 2:
                label = self._tr_cells[0].strip().rstrip(":")
                value = self._tr_cells[1].strip()
                self._assign_cor_field(label, value)
            self._tr_cells = []

        if self._in_cor_table and tag == "table":
            self._in_cor_table = False

        if tag == "li" and self._in_li:
            self._in_li = False
            text = self._li_buffer.strip()
            if text:
                self._section_items.append(text)

        if self._in_desc_div and tag == "div":
            self._desc_div_depth -= 1
            if self._desc_div_depth <= 0:
                self._in_desc_div = False
                self._in_desc_section = False
                if self._desc_buffer.strip():
                    self.course.description = self._desc_buffer.strip()

    def handle_data(self, data):
        if self._in_h1:
            self._h1_text += data
        if self._in_h2:
            self._h2_text += data
        if self._in_td:
            self._current_td_text += data
        if self._in_li:
            self._li_buffer += data
        if self._in_desc_div:
            self._desc_buffer += data

    def _parse_h1(self, text: str):
        """Parse 'C S 1A: OBJECT-ORIENTED PROGRAMMING IN JAVA' style titles."""
        match = re.match(r"^(.+?):\s*(.+)$", text)
        if match:
            self.course.code = match.group(1).strip()
            self.course.name = match.group(2).strip()
            parts = self.course.code.split()
            if len(parts) >= 2:
                self.course.department = " ".join(parts[:-1])
        else:
            self.course.name = text

    def _assign_cor_field(self, label: str, value: str):
        label_lower = label.lower()
        if "unit" in label_lower:
            self.course.units = value
        elif "hour" in label_lower:
            self.course.hours = value
        elif "advisory" in label_lower or "prerequisite" in label_lower:
            self.course.prerequisites = value
        elif "transfer" in label_lower:
            self.course.transfer_status = value
        elif "ge" in label_lower or "general education" in label_lower:
            self.course.ge_area = value
        elif "grade" in label_lower:
            self.course.grading = value

    def _flush_section(self):
        if self._current_section == "slo" and self._section_items:
            self.course.learning_outcomes = list(self._section_items)
        elif self._current_section == "objectives" and self._section_items:
            self.course.course_objectives = list(self._section_items)
        self._section_items = []
        self._current_section = None


# ── Scraping logic ─────────────────────────────────────────────────────────────

CONCURRENCY = 8
DELAY = 0.2


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch a URL with retry logic."""
    for attempt in range(3):
        try:
            resp = await client.get(url, timeout=30, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code == 404:
                return None
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error for {url} (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(1)
    return None


async def _get_all_course_links(client: httpx.AsyncClient, base_url: str) -> list[str]:
    """Get all course outline links from the /course-outlines/ index page."""
    html = await _fetch(client, f"{base_url}/course-outlines/")
    if not html:
        return []
    parser = CourseOutlineIndexParser()
    parser.feed(html)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for link in parser.links:
        if link not in seen:
            seen.add(link)
            unique.append(link)
    logger.info(f"Found {len(unique)} unique course outline links")
    return unique


async def _parse_course_page(
    client: httpx.AsyncClient, base_url: str, path: str
) -> RawCourse | None:
    """Fetch and parse a single course outline page."""
    url = urljoin(base_url, path)
    html = await _fetch(client, url)
    if not html:
        return None

    parser = CourseOutlineParser()
    try:
        parser.feed(html)
    except Exception as e:
        logger.error(f"Parse error for {url}: {e}")
        return None

    parser._flush_section()
    course = parser.course
    course.url = url

    if not course.name and not course.code:
        return None

    return course


async def _get_department_names(client: httpx.AsyncClient, base_url: str) -> dict[str, str]:
    """Scrape full department names from catalog index pages.

    Tries multiple URL patterns that CourseLeaf catalogs use:
      1. /courses-az/         (e.g., Foothill)
      2. /course-descriptions/ (e.g., Citrus)
      3. /departments/
      4. /programs/
    Returns the first one that yields results.
    """
    import html as html_mod

    candidate_paths = [
        ("/courses-az/", r'<a\s+href="/courses-az/([a-z][^/]+)/"[^>]*>([^<]+)</a>'),
        ("/course-descriptions/", r'<a\s+href="/course-descriptions/([a-z][^/]+)/"[^>]*>([^<]+)</a>'),
        ("/departments/", r'<a\s+href="/departments/([a-z][^/]+)/"[^>]*>([^<]+)</a>'),
        ("/programs/", r'<a\s+href="/programs/([a-z][^/]+)/"[^>]*>([^<]+)</a>'),
    ]

    for path, pattern in candidate_paths:
        html_text = await _fetch(client, f"{base_url}{path}")
        if not html_text:
            continue
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if not matches:
            continue

        mapping = {}
        for slug, name in matches:
            code = slug.upper().replace("-", " ")
            clean = html_mod.unescape(name.strip())
            # Strip trailing parenthetical acronym, e.g., "Accounting (ACCT)"
            clean = re.sub(r"\s*\([A-Z\s/]+\)\s*$", "", clean).strip()
            if code not in mapping:
                mapping[code] = clean
        logger.info(f"Resolved {len(mapping)} department names from {path}")
        return mapping

    logger.warning("Could not resolve department names from any catalog index page")
    return {}


async def scrape_catalog(base_url: str = "https://catalog.foothill.edu") -> list[RawCourse]:
    """
    Scrape all courses from a CourseLeaf catalog.

    Returns a list of RawCourse objects with full COR data.
    """
    base_url = base_url.rstrip("/")
    all_courses: list[RawCourse] = []

    async with httpx.AsyncClient(
        headers={"User-Agent": "Kallipolis/1.0 (educational research)"}
    ) as client:
        # Get department name mapping (acronym -> full name)
        dept_names = await _get_department_names(client, base_url)

        # Get all course outline links from the index page
        all_links = await _get_all_course_links(client, base_url)
        if not all_links:
            logger.error("No course links found. Check the catalog URL.")
            return []

        # Fetch and parse each course page with concurrency control
        sem = asyncio.Semaphore(CONCURRENCY)

        async def fetch_course(path: str) -> RawCourse | None:
            async with sem:
                course = await _parse_course_page(client, base_url, path)
                await asyncio.sleep(DELAY)
                return course

        results = await asyncio.gather(*[fetch_course(link) for link in all_links])
        for course in results:
            if course is not None:
                # Resolve department acronym to full name
                if course.department in dept_names:
                    course.department = dept_names[course.department]
                all_courses.append(course)

        logger.info(f"Successfully parsed {len(all_courses)} / {len(all_links)} courses")

    return all_courses
