"""Course outlines of record — the document a curriculum is READ FROM.

Every credit and noncredit course at a California community college has a Course
Outline of Record (Title 5 §55002): the board-approved statement of the course's
description, outcomes, objectives, content, methods and assignments. It is the one
document written at the altitude of O*NET's work activities — outcomes and objectives
are literal "students will be able to …" statements, lab content is a list of things
students do — which is why the alignment reads it and not the catalog blurb. (Read from
the SVAMP marketing document, Foothill's semiconductor certificate showed four weak
marks; read from its outlines it showed ten, eight of them outcome-level.)

There is no statewide repository of outline TEXT — COCI holds the approval record and
control codes only — so the outline lives in each college's curriculum system, and this
module has one adapter per vendor:

  courseleaf   Foothill publishes outlines as plain HTML pages under its CourseLeaf
               catalog (catalog.foothill.edu/course-outlines/<CODE>/); Coast CCD does the
               same for Orange Coast (catalog.cccd.edu/courses/<code>/) under the state's
               COR field names — one parser, a heading profile per host.
  curricunet   Ohlone's CurricUNET exposes a public course index and a per-course
               outline REPORT (a PDF) once the active `courses_id` is known.
  elumen       Mission and De Anza run eLumen. Its "Curriculum Public View" is an
               Angular app that signs in as a built-in public user before loading
               anything; this adapter makes the same three calls the page makes
               (authenticate → department courses → course) and reads the JSON.
  curriqunet   Evergreen Valley runs CurriQunet META with search disabled; its
               "All Fields" report answers anonymously by numeric entity id, and a
               cheaper companion report lets us scan ids for a discipline. San Diego CCD
               (Mesa) runs the same product with a public catalog whose subject pages
               carry each course's entity id (curriqunet_catalog_courses), so no scan.

Each adapter returns the same `Outline`: the sections we read (outcomes, objectives,
description, content, lab, assignments), the dates the college printed on it, and the
URL a reader can open. Parsers are separated from fetchers so they run on fixtures.
Retrieved outlines are cached as JSON under `courses/data/outlines/<college>/`.

Currency is checked against COCI (`ontology.coci.course_currency`), the state's record of
when the college last updated the course: an outline older than that record may have a
newer version in the college system.
"""

from __future__ import annotations

import html as htmllib
import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "data" / "outlines"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
_client = httpx.Client(headers={"User-Agent": _UA}, timeout=60, follow_redirects=True)


@dataclass
class Outline:
    college: str                 # graph college name, e.g. "Mission College"
    system: str                  # courseleaf | curricunet | elumen | curriqunet
    code: str                    # course code as the college writes it, e.g. "MTT 022"
    title: str
    description: str
    outcomes: list[str] = field(default_factory=list)      # SLOs / CSLOs — read literally
    objectives: list[str] = field(default_factory=list)    # course objectives — read literally
    content: list[str] = field(default_factory=list)       # lecture / topic outline — read for scope
    lab: list[str] = field(default_factory=list)           # lab activities — read for scope
    assignments: list[str] = field(default_factory=list)   # assignments — read for scope
    source_url: str = ""
    effective: str = ""          # the term / date the college prints as effective
    approved: str = ""           # committee or board approval date, when printed
    retrieved: str = ""          # ISO date this record was fetched
    notes: str = ""
    link_ok: bool | None = None       # the last link check's verdict (courses.outlines check), None = never checked
    link_checked: str = ""            # when              # format quirks worth carrying (e.g. "objectives field is template text")

    # the sections the matcher reads, in the two reading modes
    LITERAL = ("outcomes", "objectives")
    SCOPE = ("description", "content", "lab", "assignments")

    def sections(self) -> dict[str, str]:
        """Each section flattened to one string, for verbatim-quote gating."""
        return {"outcomes": " ".join(self.outcomes), "objectives": " ".join(self.objectives),
                "description": self.description, "content": " ".join(self.content),
                "lab": " ".join(self.lab), "assignments": " ".join(self.assignments)}

    def has(self) -> list[str]:
        return [k for k, v in self.sections().items() if v.strip()]


# ── text utilities ─────────────────────────────────────────────────────────────
def _lines(html: str) -> list[str]:
    """HTML → non-empty text lines, block tags becoming line breaks."""
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
    s = re.sub(r"<(br|/p|/li|/div|/tr|/td|/th|li|p|div|tr|h[1-6])[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s)
    return [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in s.split("\n") if l.strip()]


def _between(lines: list[str], start, stops, *, prefix: bool = False) -> list[str]:
    """Lines after the first `start` line up to the first line in `stops`."""
    def hit(l, key):
        return l.startswith(key) if prefix else l == key
    i = next((k for k, l in enumerate(lines) if hit(l, start)), None)
    if i is None:
        return []
    out = []
    for l in lines[i + 1:]:
        if any(hit(l, s) for s in stops):
            break
        out.append(l)
    return out


def _strip_enum(l: str) -> str:
    return re.sub(r"^\s*(?:[A-Za-z]|[ivxIVX]+|\d+)[.)]\s*|^\s*•\s*", "", l).strip()


def _today() -> str:
    return date.today().isoformat()


def _get(url: str, **kw) -> httpx.Response:
    """One GET, retried once on a dropped connection — catalog servers close idle keep-alive
    connections between a program's courses and the pooled client learns it the hard way."""
    try:
        return _client.get(url, **kw)
    except (httpx.RemoteProtocolError, httpx.ReadError):
        return _client.get(url, **kw)


# ── courseleaf (Foothill; Coast CCD) ───────────────────────────────────────────
FOOTHILL_URL = "https://catalog.foothill.edu/course-outlines/{code}/"
#: Each CourseLeaf catalog prints the outline under its own section headings. A profile
#: names the host's page template, how a code becomes a URL slug, and which heading holds
#: which section; the parser is the same. Foothill (the default) writes titles in capitals
#: and is title-cased on read; Coast CCD's headings are the state's COR field names.
_COURSELEAF = {
    "catalog.foothill.edu": {
        "url": FOOTHILL_URL, "slug": lambda code: code.replace(" ", "-"), "titlecase": True,
        "outcomes": "Student Learning Outcomes", "description": "Description", "objectives": "Course Objectives",
        "content": "Course Content", "lab": "Lab Content", "assignments": (),
        "heads": {"Student Learning Outcomes", "Description", "Course Objectives", "Course Content",
                  "Lab Content", "Special Facilities and/or Equipment", "Method(s) of Evaluation"},
        "effective": "Effective Term:", "approved": "",
    },
    "catalog.cccd.edu": {
        "url": "https://catalog.cccd.edu/courses/{code}/", "slug": lambda code: code.lower().replace(" ", "-"), "titlecase": False,
        "outcomes": "Course Level Student Learning Outcome(s)", "description": "Course Description", "objectives": "Course Objectives",
        "content": "Lecture Content", "lab": "Lab Content",
        "assignments": ("Reading Assignments", "Writing Assignments", "Out-of-class Assignments"),
        "heads": {"Course Description", "Course Level Student Learning Outcome(s)", "Course Objectives", "Lecture Content",
                  "Lab Content", "Method(s) of Instruction", "Instructional Techniques", "Reading Assignments",
                  "Writing Assignments", "Out-of-class Assignments", "Demonstration of Critical Thinking",
                  "Required Writing, Problem Solving, Skills Demonstration", "Eligible Disciplines", "Textbooks Resources"},
        "effective": "", "approved": "Curriculum Committee Approval Date",
    },
}
_COURSELEAF_NOISE = {"The student will be able to:", "Not applicable.", "I *Scans Competencies", "II +Scans Foundations"}


def parse_courseleaf(html: str, *, college: str, code: str, url: str, host: str = "catalog.foothill.edu") -> Outline:
    P = _COURSELEAF[host]
    L = _lines(html)
    title = next((l for l in L if re.match(rf"^{re.escape(code)}:", l)), code)
    title = title.split(":", 1)[1].strip() if ":" in title else title
    title = title.split(" < ")[0].strip()
    if P["titlecase"]:
        title = title.title()
    heads = P["heads"]

    def section(head):
        out = []
        for l in _between(L, head, heads):
            if l in _COURSELEAF_NOISE:
                continue
            # Coast CCD breaks "&nbsp;" across a tag: the line ends in "nb" and the next begins "sp;"
            if l.startswith("sp;") and out and out[-1].endswith(" nb"):
                out[-1] = out[-1][:-3].rstrip() + " " + l[3:].strip()
                continue
            out.append(l)
        return out

    slo = section(P["outcomes"])
    desc = " ".join(section(P["description"]))
    obj = section(P["objectives"])
    content = section(P["content"])
    lab = section(P["lab"])
    assign = [l for head in P["assignments"] for l in section(head)]
    eff = ""
    if P["effective"]:
        eff = next((l.split(":", 1)[1].strip() for l in L if l.startswith(P["effective"])), "")
        if not eff:  # CourseLeaf renders the field label and value on separate lines
            i = next((k for k, l in enumerate(L) if l == P["effective"]), None)
            eff = L[i + 1] if i is not None and i + 1 < len(L) else ""
    approved = ""
    if P["approved"]:
        i = next((k for k, l in enumerate(L) if l == P["approved"]), None)
        approved = L[i + 1] if i is not None and i + 1 < len(L) and re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", L[i + 1]) else ""
    return Outline(college, "courseleaf", code, title, desc, slo, obj, content, lab, assign,
                   url, eff, approved, _today())


def fetch_courseleaf(code: str, *, college: str = "Foothill College", host: str = "catalog.foothill.edu") -> Outline:
    P = _COURSELEAF[host]
    url = P["url"].format(code=P["slug"](code))
    r = _get(url)
    r.raise_for_status()
    return parse_courseleaf(r.text, college=college, code=code, url=url, host=host)


# ── curricunet (Ohlone) ────────────────────────────────────────────────────────
CURRICUNET_INDEX = "https://www.curricunet.com/{site}/search/course/course_search_result.cfm"
CURRICUNET_REPORT = "https://www.curricunet.com/{site}/reports/course_outline_report.cfm?courses_id={cid}"


def parse_curricunet_index(html: str) -> dict[str, list[tuple[int, str, str]]]:
    """{course code -> [(courses_id, status, row text)]} from the public course index.
    The index lists every version of every course; callers pick the Active one."""
    out: dict[str, list[tuple[int, str, str]]] = {}
    for row in re.split(r"<tr", html)[1:]:
        m = re.search(r"course_outline_report\.cfm\?courses_id=(\d+)", row) or \
            re.search(r"add_apr_html\.cfm\?courses_id=(\d+)", row)
        if not m:
            continue
        text = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", row))).strip()
        code = re.search(r"\b([A-Z]{2,5}) (\d{2,3}[A-Z]{0,2})\b", text)
        status = re.search(r"\*\*\s*(Active|Historical|Pending|Launched|Approved)\s*\*\*", text) or \
            re.search(r"\b(Active|Historical|Pending|Launched|Approved)\b", text)
        if code:
            out.setdefault(f"{code.group(1)} {code.group(2)}", []).append(
                (int(m.group(1)), status.group(1) if status else "?", text[:160]))
    return out


def pick_active(versions: list[tuple[int, str, str]]) -> int:
    active = [v for v in versions if v[1] == "Active"]
    return max(active or versions, key=lambda v: v[0])[0]


def pdf_text(pdf: bytes) -> str:
    """Layout-preserving text. Prefers poppler's pdftotext (the outline's two-column
    header and numbered sections survive it); falls back to pypdf."""
    try:
        p = subprocess.run(["pdftotext", "-layout", "-", "-"], input=pdf, capture_output=True, timeout=60)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.decode("utf-8", errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    import io
    from pypdf import PdfReader
    return "\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(pdf)).pages)


def parse_curricunet_outline(text: str, *, college: str, code: str, url: str) -> Outline:
    """Ohlone's OFFICIAL COURSE OUTLINE report: Roman-numbered sections, no objectives
    section (Ohlone folds objectives into its SLOs), lecture and lab content blocks."""
    t = "\n".join(re.sub(r"\s+", " ", l).strip() for l in text.split("\n") if l.strip())

    def section(start_pat, end_pat):
        m = re.search(start_pat, t)
        if not m:
            return ""
        rest = t[m.end():]
        e = re.search(end_pat, rest)
        return rest[:e.start()] if e else rest

    title = re.search(r"2\. Title: (.+?)(?=\s+\d\. |\n)", t.replace("\n", " "))
    desc = re.sub(r"\s+", " ", section(r"11\. Catalog Description:", r"\nII\.\s")).strip()
    slo_block = section(r"II\. Student Learning Outcomes\s*(?:Students will be able to:)?", r"\nIII\.\s")
    slos = [re.sub(r"^\d+\.\s*", "", re.sub(r"\s*\n\s*", " ", x)).strip()
            for x in re.split(r"\n(?=\d+\.\s)", slo_block) if x.strip()]
    content_block = section(r"III\. Course Content:", r"\nIV\.\s")
    lab_i = content_block.find("LABORATORY")
    lecture = content_block[:lab_i] if lab_i >= 0 else content_block
    lab = content_block[lab_i:] if lab_i >= 0 else ""
    clean = lambda blk: [_strip_enum(l) for l in blk.split("\n")
                         if l.strip() and l.strip() not in ("LECTURE", "LABORATORY")]
    assign = clean(section(r"IV\. Course Assignments:", r"\nV\.\s"))
    approved = re.search(r"Approval Date:\s*(\d{1,2}/\d{1,2}/\d{4})", t)
    units = re.search(r"Units:\s*([\d.]+)", t)
    return Outline(college, "curricunet", code,
                   (title.group(1).split(" Credit")[0].split(" Noncredit")[0].strip() if title else code),
                   desc, slos, [], clean(lecture), clean(lab), assign, url, "",
                   approved.group(1) if approved else "", _today(),
                   notes="no objectives section in this format" + (f"; units {units.group(1)}" if units else ""))


class CurricunetSite:
    def __init__(self, site: str = "Ohlone", college: str = "Ohlone College"):
        self.site, self.college = site, college
        self._index: dict | None = None

    def index(self) -> dict[str, list[tuple[int, str, str]]]:
        if self._index is None:
            r = _client.get(CURRICUNET_INDEX.format(site=self.site), timeout=120)
            r.raise_for_status()
            self._index = parse_curricunet_index(r.text)
        return self._index

    def fetch(self, code: str) -> Outline:
        versions = self.index().get(code)
        if not versions:
            raise KeyError(f"{code} not in the {self.site} CurricUNET index")
        cid = pick_active(versions)
        url = CURRICUNET_REPORT.format(site=self.site, cid=cid)
        r = _client.get(url, timeout=120)
        r.raise_for_status()
        return parse_curricunet_outline(pdf_text(r.content), college=self.college, code=code, url=url)


# ── elumen public curriculum view (Mission, De Anza) ───────────────────────────
ELUMEN_API = "https://api-prod.elumenapp.com:443"
#: The public view's own sign-in: a built-in public user the app authenticates as for
#: every visitor (the credential ships in its main.js). Not a person's account.
_ELUMEN_PUBLIC = {"username": "anonymous", "password": "anonymous-enclave", "rememberMe": False,
                  "email": "", "lastname": "", "firstname": ""}


def _html_list(h) -> list[str]:
    return [_strip_enum(l) for l in _lines(str(h or "")) if _strip_enum(l)]


def elumen_catalog_year(start_term: str) -> str:
    """The catalog year a start term falls in: 'Fall 2026' / '2026FA' → '2026-2027';
    'Spring 2026' / '2026SP' → '2025-2026'. '' when the term names no year."""
    m = re.search(r"(20\d\d)", start_term or "")
    if not m:
        return ""
    y = int(m.group(1))
    fall = re.search(r"fall|summer|\d{4}(FA|SU)", start_term, re.I) is not None
    return f"{y}-{y + 1}" if fall else f"{y - 1}-{y}"


def elumen_catalog_url(host: str, d: dict) -> str:
    """The tenant's public catalog page for the course's own catalog year — where De Anza
    embeds the full outline of record (every quoted sentence verified present, 2026-09-17).
    The curriculum public view cannot be deep-linked: its course route needs a session the
    app only creates from its root page, so a fresh visitor gets 'Session Expired'."""
    slug = re.sub(r"[^a-z0-9]", "", str(d.get("curriculumId") or "").lower())
    year = elumen_catalog_year((d.get("startTerm") or {}).get("name") or "")
    return f"https://{host}/catalog/{year}/course/{slug}" if slug and year else ""


def parse_elumen_course(d: dict, *, college: str, host: str, org_entity_id: int, catalog_link: bool = False) -> Outline:
    """The `/curriculum/api/courses/v2/<uuid>` record → Outline. `catalog_link` points the
    outline at the tenant's catalog course page instead of the curriculum public view — right
    where the catalog page carries the full outline (De Anza), wrong where it shows only
    outcomes and description (Mission)."""
    code = re.sub(r"\s+", " ", str(d.get("code") or "")).strip()
    code = re.sub(r"\.$", "", code)                                   # De Anza codes end in "."
    code = re.sub(r"^([A-Z]+)\s*D0*(\d)", r"\1 \2", code)             # "DMT D080" → "DMT 80"
    start = (d.get("startTerm") or {}).get("name") or ""
    committee = str(d.get("committeeApprovalDate") or "")[:10]
    url = (elumen_catalog_url(host, d) if catalog_link else "") or f"https://{host}/public/?orgEntityId={org_entity_id}&uuid={d.get('uuid')}"
    return Outline(college, "elumen", code, d.get("name") or d.get("title") or code,
                   re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", d.get("description") or ""))).strip(),
                   [c["name"] for c in d.get("csloList", []) if c.get("name")],
                   [c["name"].strip() for c in d.get("courseObjectiveList", []) if c.get("name")],
                   _html_list(d.get("courseOutline")), _html_list(d.get("labOutline")),
                   _html_list(d.get("assignments")), url, start, committee, _today())


class ElumenPublicView:
    def __init__(self, host: str, college: str):
        self.host, self.college = host, college
        self._token: str | None = None
        self._hdr = {"X-Elumen-Tenant": host, "Accept": "application/json"}

    def _auth(self) -> dict:
        if self._token is None:
            r = _client.post(f"{ELUMEN_API}/api/authenticate",
                             json={**_ELUMEN_PUBLIC, "tenantId": self.host},
                             headers={"Content-Type": "application/json"})
            r.raise_for_status()
            self._token = r.json()["id_token"]
        return {**self._hdr, "Authorization": f"Bearer {self._token}"}

    def departments(self) -> list[dict]:
        r = _client.get(f"{ELUMEN_API}/program/api/departments", headers=self._auth())
        r.raise_for_status()
        return r.json()

    def courses(self, org_entity_id: int) -> list[dict]:
        r = _client.get(f"{ELUMEN_API}/curriculum/api/courses/v2",
                        params={"department": org_entity_id, "latest": "true"}, headers=self._auth())
        r.raise_for_status()
        return r.json()

    def fetch(self, org_entity_id: int, code: str, *, catalog_link: bool = False) -> Outline:
        want = re.sub(r"[\s.]", "", code).upper()
        want_alt = re.sub(r"^([A-Z]+)(\d)", r"\1D0\2", want) if not re.search(r"[A-Z]D\d", want) else want
        match = next((c for c in self.courses(org_entity_id)
                      if re.sub(r"[\s.]", "", str(c.get("code", ""))).upper() in (want, want_alt)), None)
        if match is None:
            raise KeyError(f"{code} not in department {org_entity_id} on {self.host}")
        r = _client.get(f"{ELUMEN_API}/curriculum/api/courses/v2/{match['uuid']}", headers=self._auth())
        r.raise_for_status()
        return parse_elumen_course(r.json(), college=self.college, host=self.host, org_entity_id=org_entity_id,
                                   catalog_link=catalog_link)


# ── curriqunet META (Evergreen Valley) ─────────────────────────────────────────
CURRIQUNET_REPORT = "https://{host}/DynamicReports/AllFieldsReportByEntity/{eid}?entityType=Course&reportId={rid}"
#: Report ids are per college. Evergreen Valley: 52 = "All Fields" (the full outline),
#: 3 = "Impact" (4 KB; carries the discipline and number — the scanning report).
EVC_ALL_FIELDS, EVC_IMPACT = 52, 3

_EVC_SLO_NOISE = ("Learning Outcomes", "Assessment Methods for SLO", "Lab Activities", "Quizzes",
                  "Final Exam/Project", "Exams", "Homework", "Projects", "Written Assignments",
                  "Upon completion of this course, the student should be able to")
_EVC_SLO_NOISE_PREFIX = ("This SLO maps", "Inquiry and Reasoning", "Information Competency", "Communication:",
                         "Social Responsibility", "Personal Development", "Ethical", "Aesthetic", "SLO")


def parse_curriqunet_outline(html: str, *, college: str, url: str) -> Outline:
    """CurriQunet's "All Fields" report. The body sections vary by vintage (2021 reports
    label lecture content "(Use outline format)"), but every report ends with an ASSIST
    preview block whose labels are stable — Content, Assignments, Lab Content, Course
    Description, Objectives — so content, lab and assignments are read from there.
    Objectives come from the body's Objectives section, which on most Evergreen Valley
    outlines holds only the form's template text (then `notes` says so)."""
    L = _lines(html)
    g = lambda label, n=60: next((l[len(label):].strip()[:n] for l in L if l.startswith(label) and len(l) > len(label)), "")

    def after(label, pat=r"^\d{4}-\d{2}-\d{2}$|^\d{1,2}/\d{1,2}/\d{4}$"):
        i = next((k for k, l in enumerate(L) if l == label), None)
        return L[i + 1] if i is not None and i + 1 < len(L) and re.match(pat, L[i + 1]) else ""

    def tail_block(label, stops):
        """The block under `label` in the trailing ASSIST preview (last occurrence)."""
        idx = [k for k, l in enumerate(L) if l == label]
        if not idx:
            return []
        out = []
        for l in L[idx[-1] + 1:]:
            if l in stops:
                break
            out.append(l)
        return out

    tail_stops = {"Content", "Assignments", "Lab Content", "Course Description", "Lecture Hours", "Lab Hours",
                  "Outline Approval Date", "Outline Effective Date", "Prerequisites", "Corequisites", "Advisories",
                  "Objectives", "Instruction Methods", "Evaluation Methods", "Lecture Content", "Laboratory Content",
                  "Course Lab/Activity Content", "Other Information"}

    def value_of(label, n=120):
        """A field's value: on the label's line (Evergreen Valley) or the next line (San Diego CCD)."""
        v = g(label, n)
        if v:
            return v
        i = next((k for k, l in enumerate(L) if l == label), None)
        return L[i + 1][:n] if i is not None and i + 1 < len(L) else ""

    def tagged(tag):
        """Repeated `<tag>` / value pairs — how San Diego CCD's report lists outcomes and objectives."""
        return [L[k + 1] for k, l in enumerate(L) if l == tag and k + 1 < len(L)]

    disc, num = g("Main Course Discipline") or g("Prefix"), g("Course Number")
    code = f"{disc} {num}".strip()
    title = value_of("Course Title").split(" Short Title")[0].strip()
    desc = " ".join(_between(L, "Catalog Description", ["Short"], prefix=True))
    # Lecture content: the ASSIST tail's "Content" block (Evergreen Valley) or, where the
    # report subdivides it, its "Lecture Content" / "Laboratory Content" blocks (San Diego CCD).
    lecture_raw = tail_block("Lecture Content", tail_stops) or tail_block("Content", tail_stops)
    lecture = [_strip_enum(re.sub(r"^[IVX]+\)\s*", "", l)) for l in lecture_raw]
    lab = [_strip_enum(l) for l in tail_block("Laboratory Content", tail_stops) or tail_block("Lab Content", tail_stops)]
    assign = tail_block("Assignments", tail_stops)
    if not assign:  # no ASSIST assignments block: the body's Assignments section, its field labels dropped
        assign = [l for l in _between(L, "Assignments", ["Methods of Evaluation"])
                  if l != "Optional Text" and not l.endswith("Assignments") and not l.startswith("Appropriate ")]
    obj = tagged("Objective Text") or [l for l in _between(L, "Objectives", ["Student Learning Outcomes"])
                                       if l != "Objectives" and not l.startswith(("Objectives are small steps", "Objectives need to be"))]
    slo = tagged("Outcome Text") or [l for l in _between(L, "Student Learning Outcomes", ["Methods of Evaluation and Examination"])
                                     if l not in _EVC_SLO_NOISE and not l.startswith(_EVC_SLO_NOISE_PREFIX) and len(l) > 25]
    notes = "objectives field holds template text only" if not obj else ""
    return Outline(college, "curriqunet", code, title, desc, slo, obj, lecture, lab, assign, url,
                   after("Outline Effective Date"), after("Outline Approval Date") or after("Revision Date"),
                   _today(), notes)


def fetch_curriqunet(entity_id: int, *, host: str = "evc.curriqunet.com", college: str = "Evergreen Valley College",
                     report_id: int = EVC_ALL_FIELDS) -> Outline:
    url = CURRIQUNET_REPORT.format(host=host, eid=entity_id, rid=report_id)
    r = _get(url)
    r.raise_for_status()
    return parse_curriqunet_outline(r.text, college=college, url=url)


CURRIQUNET_CATALOG_PAGE = "https://{host}/Catalog/_getPage?catalogId={catalog_id}&id={page_id}"


def parse_curriqunet_catalog_courses(page: dict) -> dict[str, dict]:
    """{code: {"entity_id", "title", "description"}} from a CurriQunet META catalog subject page
    (the JSON behind `catalog/alias/<catalog>/iq/<page_id>`). The page's curriculum block
    renders one `course-summary-wrapper` per course carrying its entity id — the key the
    "All Fields" report is addressed by. Only status Active rows are returned."""
    out: dict[str, dict] = {}
    for block in page.get("body", []):
        if block.get("presentationtype") != "curriculum":
            continue
        for m in re.finditer(r'<div class="[^"]*course-summary-wrapper[^"]*" data-course-id="(\d+)"(.*?)(?=<div class="[^"]*course-summary-wrapper|$)',
                             block.get("text") or "", re.S):
            eid, body = int(m.group(1)), m.group(2)
            status = re.search(r'data-catalog-status-base="([^"]*)"', body)
            if status and status.group(1) != "Active":
                continue
            field = lambda cls: htmllib.unescape(re.sub(r"<[^>]+>", "", (re.search(rf'class="{cls}"[^>]*>(.*?)</', body, re.S) or [None, ""])[1])).strip()
            code = f'{field("course-subject-code")} {field("course-number")}'.strip()
            if code:
                out[code] = {"entity_id": eid, "title": field("course-title"), "description": field("course-description")}
    return out


def curriqunet_catalog_courses(host: str, catalog_id: int, page_id: int) -> dict[str, dict]:
    """Fetch and parse one catalog subject page (see parse_curriqunet_catalog_courses)."""
    r = _get(CURRIQUNET_CATALOG_PAGE.format(host=host, catalog_id=catalog_id, page_id=page_id),
             headers={"Accept": "application/json"})
    r.raise_for_status()
    return parse_curriqunet_catalog_courses(r.json())


def scan_curriqunet(discipline: str, id_range: range, *, host: str = "evc.curriqunet.com",
                    impact_report_id: int = EVC_IMPACT) -> list[int]:
    """Entity ids in `id_range` whose light report names `discipline`. Slow (one request
    per id); use once to seed a roster, then pin the ids."""
    hits = []
    for eid in id_range:
        r = _client.get(CURRIQUNET_REPORT.format(host=host, eid=eid, rid=impact_report_id), timeout=20)
        if r.status_code == 200 and discipline in r.text:
            hits.append(eid)
    return hits


# ── cache + dispatch ──────────────────────────────────────────────────────────
def _cache_path(college_key: str, code: str) -> Path:
    return CACHE_DIR / college_key / (re.sub(r"[^A-Za-z0-9]+", "-", code).strip("-") + ".json")


def save(outline: Outline, college_key: str) -> Path:
    p = _cache_path(college_key, outline.code)
    p.parent.mkdir(parents=True, exist_ok=True)
    d = asdict(outline)
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def load(college_key: str, code: str) -> Outline | None:
    p = _cache_path(college_key, code)
    if not p.exists():
        return None
    return Outline(**json.loads(p.read_text(encoding="utf-8")))


def retrieve(source: dict, code: str, *, college: str, college_key: str, refresh: bool = False,
             title: str = "") -> Outline:
    """Fetch (or load from cache) one outline. `source` is the roster's adapter spec:
      {"system": "courseleaf"}                                   (Foothill; or "host": "catalog.cccd.edu")
      {"system": "curricunet", "site": "Ohlone"}
      {"system": "elumen", "host": "mission.elumenapp.com", "org_entity_id": 200}
      {"system": "curriqunet", "host": "evc.curriqunet.com", "entity_id": 5299, "report_id": 52}
    """
    if not refresh:
        cached = load(college_key, code)
        if cached is not None:
            return cached
    sysname = source["system"]
    if sysname == "courseleaf":
        o = fetch_courseleaf(code, college=college, host=source.get("host", "catalog.foothill.edu"))
    elif sysname == "curricunet":
        o = CurricunetSite(source.get("site", "Ohlone"), college).fetch(code)
    elif sysname == "elumen":
        o = ElumenPublicView(source["host"], college).fetch(int(source["org_entity_id"]), code,
                                                             catalog_link=bool(source.get("catalog_link")))
        o.code = code                                   # keep the roster's spelling
    elif sysname == "curriqunet":
        o = fetch_curriqunet(int(source["entity_id"]), host=source.get("host", "evc.curriqunet.com"),
                             college=college, report_id=int(source.get("report_id", EVC_ALL_FIELDS)))
        o.code = code
    else:
        raise ValueError(f"unknown outline system {sysname!r}")
    if title:
        o.title = title
    save(o, college_key)
    return o


# ── link check ─────────────────────────────────────────────────────────────────
#: Where a rendered page is needed to see anything at all (single-page apps).
_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _rendered_text(url: str, budget_ms: int = 20000) -> str:
    """The page's text after its scripts have run — headless Chrome, when installed."""
    import shutil
    import subprocess
    exe = _CHROME if Path(_CHROME).exists() else shutil.which("google-chrome") or shutil.which("chromium")
    if not exe:
        raise RuntimeError("no headless browser for a single-page app link")
    dom = subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", f"--virtual-time-budget={budget_ms}",
                          "--dump-dom", url], capture_output=True, text=True, timeout=120).stdout
    return htmllib.unescape(re.sub(r"<[^>]+>", " ", dom))


def check_link(o: Outline) -> tuple[bool, str]:
    """Does the outline's link land on a page that NAMES the course? A reader clicks a chip
    to check a quote at the source; a link that resolves to a listing, a shell or a stale
    page is a broken promise the HTTP status alone cannot see. Plain pages and PDFs are read
    as fetched; single-page apps (eLumen) are rendered first."""
    import subprocess
    import tempfile
    key = re.sub(r"[\s.]", "", o.code).lower()
    dept, num = re.match(r"^([A-Za-z ]+?)\s*(\d.*)$", o.code).groups() if re.match(r"^([A-Za-z ]+?)\s*(\d.*)$", o.code) else (o.code, "")
    try:
        if o.system == "elumen":
            text = _rendered_text(o.source_url)
            if "Session Expired" in text:
                return False, "session expired: the public view cannot be deep-linked"
        else:
            r = _get(o.source_url)
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}"
            if "pdf" in r.headers.get("content-type", ""):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
                    t.write(r.content)
                text = subprocess.run(["pdftotext", "-l", "2", t.name, "-"], capture_output=True, text=True).stdout
            else:
                text = htmllib.unescape(re.sub(r"<[^>]+>", " ", r.text))
    except Exception as e:  # noqa: BLE001 — the verdict is the point; the reason travels with it
        return False, f"{type(e).__name__}: {e}"[:120]
    flat = re.sub(r"[\s.]", "", text).lower()
    named = key in flat or (num and re.search(rf"{re.escape(dept.strip())}\s*-?\s*D?0*{re.escape(num)}", text, re.I) is not None)
    if not named:
        return False, "page does not name the course"
    if o.outcomes and not any(_norm_text(x) in _norm_text(text) for x in o.outcomes[:3]):
        return True, "names the course; none of its first outcomes found on the page"
    return True, "names the course and carries its outcomes"


def _norm_text(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()


def check_cached(college_key: str | None = None) -> list[tuple[str, str, bool, str]]:
    """Check every cached outline's link (one college, or all) and stamp the verdict into
    the cache file. Returns (college_key, code, ok, detail) rows."""
    rows = []
    for d in sorted(CACHE_DIR.glob("*") if college_key is None else [CACHE_DIR / college_key]):
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            o = Outline(**json.loads(f.read_text(encoding="utf-8")))
            ok, why = check_link(o)
            o.link_ok, o.link_checked = ok, _today()
            f.write_text(json.dumps(o.__dict__, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            rows.append((d.name, o.code, ok, why))
            print(f"{'ok ' if ok else 'BAD'} {d.name:9s} {o.code:10s} {why}", flush=True)
    return rows


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Course outlines of record: check that every cached outline's link lands on its course.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="fetch (or render) each cached outline's link and stamp link_ok / link_checked into the cache")
    c.add_argument("college_key", nargs="?", help="one college's cache directory; default all")
    a = ap.parse_args()
    rows = check_cached(a.college_key)
    bad = [r for r in rows if not r[2]]
    print(f"{len(rows) - len(bad)} ok, {len(bad)} not landing on the course")
    raise SystemExit(1 if bad else 0)
