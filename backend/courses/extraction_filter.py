"""Catalog-extraction artifact filter.

The PDF-extraction stage (`backend/courses/scrape_pdf.py`) emits one row
per "course" Gemini identifies. The system prompt asks Gemini to skip
program-requirement tables, but it routinely violates that instruction
when a credentials/degree section has prose descriptions ("Prepares
students for entry-level positions in small business accounting…").
Those credential rows then become real `:Course` nodes in Neo4j with
no TOP code, since the MCF has nothing to match — credentials aren't
courses, so the Chancellor's Office never assigned them a TOP6.

This module is the deterministic guard. It runs once after Gemini's
output (in `scrape_pdf.py`) and drops rows whose `code`/`name` shape
matches a known artifact pattern. The audit at
`tools/courses-audit/classify_unmapped.py` re-uses the same predicates
so that filter-time and audit-time agree on what "is a course" means.

What this module rejects:

  - Codes with broken shape: pure-numeric ("104"), prefix-only ("THEA"),
    `?`-containing ("???? 101"), or mid-code lowercase fragments
    ("PSYC C1000mtroduction"). These are scrape garbage.
  - Names that contain credential vocabulary (`Associate in Arts`,
    `Associate in Science`, `AA-T`, `AS-T`, `Certificate of Achievement`,
    `Skills Competency Award`, `Department Award`, `, Level I`/`II`/`III`/
    `IV`). These are degree/cert listings, not courses.
  - Codes matching CSU/UC C-ID patterns (`C\d{4}`, optionally with an
    English prefix like "Communication C1000"). C-IDs are intersegmental
    transfer-course aliases, not local catalog codes.
  - Codes whose alpha prefix matches a non-CCC institution
    (`UNR ENG`, `CSU …`, `UC[A-Z]?`). Lassen lists UNR cross-enrollment
    courses; they aren't California Community College courses.

What this module DELIBERATELY does NOT reject:

  - Real courses whose specific `(prefix, num)` pair isn't in the MCF
    yet. That's MCF lag (Berkeley City's COMM 020 is a real course;
    the MCF data file just predates the renumbering). The MCF lookup
    will return None for those, but they belong in the graph and the
    audit categorizes them separately.
  - English-name-prefix codes ("Biology 1") at colleges where the
    catalog uses long prefixes. These ARE courses; the lookup logic
    in `mcf_lookup.py` resolves them via the fullname-prefix mapping.

Design constraint: filter-time predicates must not require an MCF
lookup. The MCF is loaded per-college in `mcf_lookup.py` and is
load-bearing for the audit, but extraction runs in the PDF-scrape
pipeline before TOP6 assignment, so we can't depend on MCF here.
"""
from __future__ import annotations

import re


# Tokens in a course name that imply this row is a credential listing,
# not a course. Order matters only in that more-specific phrases are
# listed first for readability — every row is checked against every
# marker.
DEGREE_NAME_MARKERS: tuple[str, ...] = (
    "Certificate of Completion",
    "Certificate of Achievement",
    "Skills Competency Award",
    "Associate in Arts for Transfer",
    "Associate in Science for Transfer",
    "Associate in Arts (AA)",
    "Associate in Science (AS)",
    "Associate in Arts",      # bare form, e.g. "Accounting, Associate in Arts"
    "Associate in Science",   # bare form
    "AA-T",
    "AS-T",
    "Department Award",
    ", Certificate",
    ", Level I",
    ", Level II",
    ", Level III",
    ", Level IV",
)

# Code prefixes from non-CCC institutions. Used by colleges with cross-
# enrollment relationships (Lassen ↔ UNR for the Nevada border case).
NON_CCC_PREFIX_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"^UNR\b"),
    re.compile(r"^CSU\b"),
    re.compile(r"^UC[A-Z]?\b"),
)

# C-ID intersegmental transfer course identifier. "C1000" is a C-ID
# alone; "Communication C1000" is the same C-ID prefixed with an
# English subject name. Either way it's not a local enrollable code.
_CID_FULL = re.compile(r"^C\d{4}[A-Z]?$", re.IGNORECASE)
_CID_WITH_ENGLISH = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+C\d{4}[A-Z]?$"
)

# An English-name course code prefix ("Administration of Justice 12",
# "Biology 1"). NOT a reject pattern — used here only to whitelist
# fullname-prefix codes against the "lowercase fragment in code"
# garbage rule, since fullname-prefix codes legitimately contain
# lowercase letters.
_FULLNAME_PREFIX = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Za-z][a-z]*)*)\s+(\d+[A-Z\.\d]*)$"
)


def is_artifact(code: str, name: str) -> tuple[bool, str]:
    """Return (True, reason) if (code, name) represents a catalog-
    extraction artifact rather than a real course; (False, "") otherwise.

    The reason string is short and stable — it's logged in the
    extraction meta and can be aggregated across runs to track which
    artifact patterns dominate at which colleges.
    """
    raw = (code or "").strip()
    full_name = (name or "").strip()

    # ── 1. Code-shape artifacts ────────────────────────────────────────
    # Short codes that aren't real course identifiers. The lower bounds
    # used to be 2 (digits) / 2 (letters), but SBCC's catalog produced
    # single-char "codes" like "9" (name: "Santa Barbara City College")
    # and "T" (name: "Teaching with Humanizing Technology") — clearly
    # page fragments, not courses.
    if re.fullmatch(r"\d{1,4}", raw):
        return (True, "pure_numeric_code")
    if re.fullmatch(r"[A-Z]{1,8}", raw):
        return (True, "prefix_only_no_number")
    if "?" in raw:
        return (True, "code_contains_question_mark")
    # Greek-letter (or other non-ASCII) prefix that visually mimics
    # a Latin-letter code. We've observed Gemini emit duplicates like
    # "ΑΝΤΗ 102" (Greek Α-Ν-Τ-Η, codepoints 913/925/932/919) alongside
    # the real "ANTH 102" (Latin A-N-T-H). The Greek twin has no MCF
    # match because the bytes differ; the Latin twin is the real row.
    if any(ord(ch) > 127 for ch in raw):
        return (True, "non_ascii_code_chars")

    # ── 2. Name-shape artifacts: credential/degree listings ────────────
    for marker in DEGREE_NAME_MARKERS:
        if marker in full_name:
            return (True, f"degree_name_marker:{marker!r}")

    # ── 3. Non-CCC institution prefix ──────────────────────────────────
    for pat in NON_CCC_PREFIX_PATTERNS:
        if pat.match(raw):
            return (True, f"non_ccc_prefix:{pat.pattern}")

    # ── 4. C-ID transfer-course identifier ─────────────────────────────
    if _CID_FULL.fullmatch(raw):
        return (True, "cid_alone")
    if _CID_WITH_ENGLISH.fullmatch(raw):
        return (True, "cid_with_english_prefix")

    # ── 5. Mid-code lowercase fragments (scrape garbage) ───────────────
    # English-name prefixes ("Administration of Justice 12") legitimately
    # contain lowercase. Whitelist those before the garbage check.
    if not _FULLNAME_PREFIX.match(raw) and re.search(r"[a-z]{3,}", raw):
        return (True, "lowercase_fragment_in_code")

    return (False, "")


def filter_extracted(
    rows: list[dict],
) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Partition Gemini-extracted course rows into kept and dropped.

    Returns:
        kept    — rows that pass the artifact filter (real courses)
        dropped — list of (row, reason) for the rows we removed

    The dropped list is what the caller logs into extraction_meta.json
    so a future audit can see *why* a row was rejected and how many
    rows match each pattern at each college.
    """
    kept: list[dict] = []
    dropped: list[tuple[dict, str]] = []
    for row in rows:
        is_art, reason = is_artifact(row.get("code", ""), row.get("name", ""))
        if is_art:
            dropped.append((row, reason))
        else:
            kept.append(row)
    return kept, dropped
