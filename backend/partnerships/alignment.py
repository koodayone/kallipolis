"""Curriculum alignment — which courses carry the work of the target occupation.

Three shapes. A PROGRAM RECORD (data/programs/<college_key>-<slug>.json) names one
certificate: the college, the COCI award it is, and its courses. A ROSTER
(data/<roster>.json) connects records to occupations — a consortium report's roster lists
one program per college; a program evaluation's roster lists the one program under review
and shares the def's slug. A READING is one record read against one occupation from its
course outlines of record: activities down the side (derived importance order), the
program's courses across the top, and a mark wherever a course's outline evidences an
activity — solid where an outcome or objective states it, a ring where the description,
content, lab or assignments involve it. Every mark carries the sentence it rests on.
Readings are stored per record (saved_reports/alignment/<ref>.json), so a reading made once
serves every roster that cites the program, and a program shows the same marks in every
document that carries it.

THE EDITORIAL RULES (locked 2026-09-16; change them here, not in prose):

  unit        the O*NET detailed work activity; rows = activities anchored to the
              occupation's Core tasks, in O*NET's importance order, no numbers shown
  record      identity lives in the record; a roster only connects it to occupations
              (paired_soc, reads_against, review_socs). A record's course-code spelling
              is a KEY: adapters keep it and saved marks are keyed by it, so renaming a
              code orphans its marks
  pairing     CHOSEN from the program's stated purpose (roster `paired_soc`); the
              TOP→CIP→SOC crosswalk's verdict is shown beside it, never used to choose.
              An evaluation roster's occupations come from its def's derived `socs` — one
              occupation list per document
  evidence    course outlines of record only, retrieved from the college's curriculum
              system (courses.outlines) and checked against COCI for currency
  reading     outcomes / program outcomes / objectives → LITERAL → solid (level 2)
              description / content / lab / assignments → SCOPE → ring (level 1)
              a ring never becomes solid by inference
  gate        every match quotes a verbatim phrase; the quote must be found in the named
              course's outline or the match is dropped (fail-closed); the LEVEL is set
              by the section the quote is actually found in, not the one claimed
  adjudicate  a second pass reviews each gated match against the activity's task text
              and drops the disputed ones; drops are logged for the review file
  merge       sources union; the strongest level wins; evidence is deduplicated by quote
  lead        per activity, ONE excerpt is chosen as the mark a reviewer points to first:
              a final LLM pass judges which verified excerpt most specifically states the
              activity as the task defines it; tier breaks ties (an SLO or objective over
              content). Stored on the row and KEPT, like a mark, while it is still among
              the row's excerpts; only rows whose excerpts changed are re-judged on a
              re-read (`--rerank` re-judges every row). A certificate column shows the lead
  accumulate  a re-run UNIONS with the saved alignment: the proposer is stochastic, so a
              match found once (gated, adjudicated) is kept until a human removes it
              from the saved file; drops are logged, never applied retroactively
  score       none — counts of activities, per-course footers, named gaps

The matcher is an LLM under the subscription (`llm.claude_cli`), because outcomes and
activities share a grammar but not a vocabulary: colleges write "troubleshoot",
"construct", "interpret"; O*NET writes "diagnose", "fabricate", "review". Only about a
quarter of outcome verbs appear in O*NET text at all, so lexical matching misses most
true matches. The gate is what keeps the judgment honest.

Vocabulary: in prose a "competency" IS a work activity; programs are never "feeders".
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING
from datetime import date
from pathlib import Path

from courses.outlines import Outline, retrieve
from occupations.descriptions import get_title
from occupations.work_activities import ONET_VINTAGE, WorkActivity, get_work_activities

if TYPE_CHECKING:
    from ontology.coci import CociAward

logger = logging.getLogger(__name__)

DATA = Path(__file__).parent / "data"
SAVED = Path(__file__).parent / "saved_reports"

LEVEL = {"outcomes": 2, "objectives": 2, "program_outcomes": 2,
         "description": 1, "content": 1, "lab": 1, "assignments": 1}
SECTION_LABEL = {"outcomes": "SLO", "objectives": "Objective", "program_outcomes": "Program outcome",
                 "description": "Description", "content": "Content outline", "lab": "Lab content",
                 "assignments": "Assignment"}
PLO = "PLO"   # the pseudo-course for the certificate's own outcomes


# ── records and rosters ────────────────────────────────────────────────────────
PROGRAMS = DATA / "programs"
STORE = SAVED / "alignment"


def load_roster(roster_id: str) -> dict:
    p = DATA / f"{roster_id.replace('-', '_')}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_program(ref: str) -> dict:
    """A program record by ref — its file stem, e.g. 'foothill-semiconductor-processing'."""
    return json.loads((PROGRAMS / f"{ref}.json").read_text(encoding="utf-8"))


def roster_programs(roster: dict) -> list[dict]:
    """Each roster entry resolved: the record's fields, the entry's connection fields over
    them, and `ref`."""
    return [{**load_program(e["program"]), **e, "ref": e["program"]} for e in roster["programs"]]


def program_outlines(program: dict, *, refresh: bool = False) -> dict[str, Outline]:
    """{course code -> Outline} for every course in the program, from cache or the
    college system. Per-course adapter overrides (`course_sources`) win over the
    program default (`source`)."""
    out = {}
    for c in program["courses"]:
        src = (program.get("course_sources") or {}).get(c["code"], program["source"])
        out[c["code"]] = retrieve(src, c["code"], college=program["college"],
                                  college_key=program["college_key"], refresh=refresh, title=c.get("title", ""))
    return out


# ── the two prompts ────────────────────────────────────────────────────────────
MATCH_SYSTEM = """You audit a community-college certificate against the core work activities of one occupation, using the colleges' official Course Outlines of Record.

Each course has several kinds of text, read differently:
- SLO (student learning outcomes) and OBJECTIVE ("the student will be able to…"): read LITERALLY. They evidence an activity when they state that students perform the activity or a directly constitutive component of it. section = "outcomes" or "objectives".
- DESCRIPTION, CONTENT (lecture topic outline), LAB (laboratory activities) and ASSIGNMENT: read for SCOPE. They evidence an activity when the course, as described or outlined, plainly involves doing that activity in this occupation's setting. Use the O*NET task text to decide what the activity concretely means for this occupation, then ask whether a student covering this content would do it. The inference must run through the technical content itself (a content line "Vacuum wands" under "Moving wafers" evidences placing wafers with a vacuum wand; a generic line like "Stay alert" does not). section = "description", "content", "lab" or "assignments".
- The certificate's PROGRAM OUTCOMES are read literally; course = "PLO", section = "program_outcomes".

Do not credit general academic outcomes (communication, teamwork, ethics, study skills, career exploration) to technical activities. Do not credit an activity the course could only touch incidentally. Match only the activity's action, not a precondition for it: understanding contamination does not evidence recommending process improvements.

Every match carries a VERBATIM quote (under 25 words) copied exactly from the named course and section, plus a one-clause basis. Prefer the strongest section available (outcomes/objectives over content) but list up to two supporting quotes per activity when they come from different courses. Be generous in recall within these rules; the quotes will be checked mechanically and unverifiable ones dropped."""

MATCH_SCHEMA = {
    "type": "object",
    "properties": {"matches": {"type": "array", "items": {
        "type": "object",
        "properties": {"activity": {"type": "integer"}, "course": {"type": "string"},
                       "section": {"type": "string", "enum": list(LEVEL)},
                       "quote": {"type": "string"}, "basis": {"type": "string"}},
        "required": ["activity", "course", "section", "quote", "basis"], "additionalProperties": False}}},
    "required": ["matches"], "additionalProperties": False}

ADJUDICATE_SYSTEM = """You are the second reader on a curriculum-alignment audit. Each proposed match pairs a verbatim quote from a course outline (already verified to exist in the named section) with an O*NET work activity and the task statement that DEFINES that activity for this occupation.

The task text is the definition. A quote that evidences the task evidences the activity: if the task says "using vacuum wand or tweezers" and the course content lists "Vacuum wands" under wafer handling, that is a match. Read literal sections (outcomes, objectives, program outcomes) as commitments — the quote must state the activity or a directly constitutive step of it, in the task's terms. Read scope sections (description, content, lab, assignments) as what the course covers — the quote must name technical content that a student doing this task would do or use.

DROP only for one of these four reasons, and name which:
  (a) topic-only: the quote names a subject or heading with no performable content that maps onto the task ("Photolithography" alone; "Reliability")
  (b) precondition: the quote names knowledge that precedes the activity rather than the activity ("understand contamination" for recommending process changes)
  (c) generic: a general academic or workplace skill (communication, teamwork, safety awareness, study skills) credited to a technical activity
  (d) different activity: the quote clearly evidences a different work activity than the one proposed. This never applies when the quote evidences one of the TASKS listed under the activity — O*NET's task-to-activity mapping is authoritative, whatever the activity's title suggests.
Otherwise KEEP. Do not drop a match because the course is introductory, because the quote is short, or because the wording differs from O*NET's — vocabulary differs by design.

Return every match id with keep=true or keep=false and a one-clause reason that starts with the letter of the rule when dropping."""

ADJUDICATE_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "integer"}, "keep": {"type": "boolean"}, "reason": {"type": "string"}},
        "required": ["id", "keep", "reason"], "additionalProperties": False}}},
    "required": ["verdicts"], "additionalProperties": False}

RANK_SYSTEM = """You are the final reader on a curriculum-alignment audit. For one occupation, each work activity below lists the verbatim outline excerpts (already verified and adjudicated) that evidence it, each from a named course and a named section of that course's Course Outline of Record.

For each activity choose the ONE excerpt that most specifically states the activity as the occupation's task text defines it — the sentence a reviewer would point to first. Judge the excerpt, not the course: a short content line that names the exact procedure beats a longer objective about something adjacent. When two excerpts state the activity equally well, prefer the higher section tier: an SLO or objective (the course commits to it) over a description, content, lab or assignment line (the course covers it).

Return every activity id with the chosen excerpt id and a one-clause reason."""

RANK_SCHEMA = {
    "type": "object",
    "properties": {"choices": {"type": "array", "items": {
        "type": "object",
        "properties": {"activity": {"type": "integer"}, "excerpt": {"type": "integer"}, "reason": {"type": "string"}},
        "required": ["activity", "excerpt", "reason"], "additionalProperties": False}}},
    "required": ["choices"], "additionalProperties": False}


def _program_text(program: dict, outlines: dict[str, Outline]) -> str:
    L = [f"CERTIFICATE: {program['certificate']} ({program['college']})",
         f"CERT DESCRIPTION: {program.get('program_description', '')}"]
    L += [f"PLO: {x}" for x in program.get("program_outcomes", [])]
    for c in program["courses"]:
        o = outlines[c["code"]]
        L.append(f"\nCOURSE {c['code']} — {o.title}")
        L.append(f"  DESCRIPTION: {o.description}")
        L += [f"  SLO: {s}" for s in o.outcomes]
        L += [f"  OBJECTIVE: {s}" for s in o.objectives]
        if o.content:
            L += ["  CONTENT:"] + [f"    - {s}" for s in o.content]
        if o.lab:
            L += ["  LAB:"] + [f"    - {s}" for s in o.lab]
        if o.assignments:
            L += ["  ASSIGNMENT:"] + [f"    - {s}" for s in o.assignments]
    return "\n".join(L)


def _activities_text(occ_title: str, soc: str, acts: list[WorkActivity]) -> str:
    rows = [f"{i + 1}. {a.dwa}\n   task: {a.task_text}" for i, a in enumerate(acts)]
    return f"=== OCCUPATION: {occ_title} (SOC {soc}) — core work activities ===\n" + "\n".join(rows)


# ── gate ───────────────────────────────────────────────────────────────────────
_norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


@dataclass
class Match:
    activity: int            # 0-based index into the plate's activity list
    course: str              # course code or "PLO"
    section: str             # the section the quote was FOUND in
    level: int               # LEVEL[section]
    quote: str
    basis: str
    claimed_section: str = ""
    kept: bool = True
    verdict: str = ""        # adjudicator's reason (kept or dropped)


def gate(raw_matches: list[dict], program: dict, outlines: dict[str, Outline], n_activities: int) -> tuple[list[Match], list[dict]]:
    """Fail-closed verbatim check. A quote must be found in the named course's outline;
    the section it is found in sets the level. Returns (kept, dropped)."""
    plo_text = _norm(" ".join(program.get("program_outcomes", [])))
    key = lambda c: re.sub(r"[^a-z0-9]", "", c.lower())
    codes = {key(c): c for c in outlines}
    kept, dropped = [], []
    for m in raw_matches:
        i = int(m.get("activity", 0)) - 1
        q = _norm(m.get("quote", ""))
        if not (0 <= i < n_activities) or len(q) < 8:
            dropped.append({**m, "why": "malformed"}); continue
        course = str(m.get("course", "")).strip()
        cert = _norm(program.get("certificate", ""))
        if course.upper().startswith(PLO) or m.get("section") == "program_outcomes" or (cert and _norm(course) == cert):
            # the certificate's own outcomes: the matcher writes "PLO", or the certificate's name
            if q in plo_text:
                kept.append(Match(i, PLO, "program_outcomes", 2, m["quote"], m.get("basis", ""), m.get("section", "")))
            else:
                dropped.append({**m, "why": "quote not in program outcomes"})
            continue
        code = codes.get(key(course)) or next((c for k, c in codes.items() if key(course).startswith(k) or k.startswith(key(course))), None)
        if code is None:
            dropped.append({**m, "why": f"unknown course {course!r}"}); continue
        secs = outlines[code].sections()
        claimed = m.get("section", "")
        found = claimed if q in _norm(secs.get(claimed, "")) else next((s for s, t in secs.items() if q in _norm(t)), None)
        if found is None:
            dropped.append({**m, "why": "quote not verbatim in that course"}); continue
        kept.append(Match(i, code, found, LEVEL[found], m["quote"], m.get("basis", ""), claimed))
    return kept, dropped


# ── result shapes ──────────────────────────────────────────────────────────────
@dataclass
class Evidence:
    course: str
    section: str
    level: int
    quote: str
    basis: str


@dataclass
class Cell:
    level: int
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class Row:
    dwa_id: str
    dwa: str
    task: str
    cells: dict[str, Cell] = field(default_factory=dict)     # course code -> Cell (PLO included)
    lead: dict | None = None                                 # {course, section, quote, reason}: the excerpt shown first

    @property
    def level(self) -> int:
        return max((c.level for c in self.cells.values()), default=0)


@dataclass
class Plate:
    college: str
    member_id: str
    certificate: str
    kind: str
    top6: str | None
    top_name: str
    paired_soc: str
    occupation: str
    crosswalk_socs: list[str]
    pairing_basis: str
    courses: list[dict]                       # [{code, title, units, source_url, effective, approved, sections, currency}]
    program_outcomes: list[str]
    rows: list[Row]
    dropped: list[dict] = field(default_factory=list)   # gate + adjudication drops, for the review file
    source_note: str = ""
    role: str = ""              # paired | crosswalk | review — how the roster connects the program to this occupation; set by view_roster, never stored
    short_title: str = ""       # the award's COCI title — the column label when a roster's columns are certificates

    def counts(self) -> dict:
        n = len(self.rows)
        return {"activities": n,
                "outcome_level": sum(1 for r in self.rows if r.level == 2),
                "any_evidence": sum(1 for r in self.rows if r.level >= 1),
                "per_course": {c["code"]: sum(1 for r in self.rows if c["code"] in r.cells) for c in self.courses}}


# ── the run ────────────────────────────────────────────────────────────────────
def align_program(program: dict, *, soc: str, refresh: bool = False,
                  adjudicate: bool = True, complete=None, coci_rows: list[dict] | None = None,
                  units: str = "all") -> Plate:
    """Read one program RECORD against one occupation. The plate carries what the reading
    found and nothing of how a roster connects the program to the occupation (role, pairing
    basis, crosswalk) — `view_roster` is the only writer of those. `complete` is the LLM
    seam (llm.claude_cli.complete by default); `coci_rows` the college's COCI course export
    if a currency check is wanted. `units="plo"` reads only the certificate's own program
    outcomes — a cheap re-read that unions into the saved plate."""
    if complete is None:
        from llm.claude_cli import complete as _c
        complete = _c
    acts = get_work_activities(soc)
    occ_title = get_title(soc) or soc
    outlines = program_outlines(program, refresh=refresh)

    acts_text = _activities_text(occ_title, soc, acts)
    # Two proposers, one gate. A whole program in one prompt under-proposes for large
    # programs (Mission's twelve outlines in one call drew 21 proposals; course by
    # course they drew 81) while a lone course loses the certificate's framing (Foothill
    # drew 23 as a program and 10 course by course). Their union is what the gate and
    # the adjudicator then discipline. The certificate's own outcomes get a call too.
    units_: list[tuple[str, str]] = [("program", _program_text(program, outlines))] if units == "all" else []
    if program.get("program_outcomes"):
        # Its own unit, and an explicit one: given bare PLO lines under the course-shaped
        # rubric the matcher proposed nothing at all (Foothill's four programs, 2026-09-17),
        # or named the certificate as the course (Ohlone). Say what the unit is and how to
        # label a match.
        units_.append((PLO, f"CERTIFICATE: {program['certificate']} ({program['college']})\n"
                       "This unit holds ONLY the certificate's PROGRAM LEARNING OUTCOMES (no courses). Read each literally: a "
                       "PLO evidences an activity when it states that graduates perform the activity or a directly constitutive "
                       f"component of it. For every match, course = \"{PLO}\", section = \"program_outcomes\", quote = a "
                       "verbatim phrase of the PLO.\n" + "\n".join(f"PLO: {x}" for x in program["program_outcomes"])))
    if units == "all":
        for c in program["courses"]:
            units_.append((c["code"], _program_text({**program, "courses": [c], "program_outcomes": []}, outlines)))
    units = units_
    if not units:
        rows = [Row(a.dwa_id, a.dwa, a.task_text) for a in acts]
        return Plate(program["college"], program["member_id"], program["certificate"], program.get("kind", "credit"),
                     program.get("top6"), program.get("top_name", ""), soc, occ_title, [], "", [],
                     program.get("program_outcomes", []), rows, short_title=program.get("short_title", ""))

    def _match(unit):
        code, text = unit
        label = "PROGRAM OUTCOMES" if code == PLO else "PROGRAM TEXT"
        r = complete(MATCH_SYSTEM, f"{acts_text}\n\n=== {label} ({code}) ===\n{text}", MATCH_SCHEMA)
        if r["data"] is None:
            logger.warning("matcher failed for %s %s: %s", program["college"], code, r["error"])
            return []
        return r["data"]["matches"]

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        proposed = [m for batch in ex.map(_match, units) for m in batch]
    kept, dropped = gate(proposed, program, outlines, len(acts))
    logger.info("%s vs %s: %d proposed over %d calls, %d gated in, %d dropped",
                program["college"], soc, len(proposed), len(units), len(kept), len(dropped))

    if adjudicate and kept:
      try:
        items = "\n".join(
            f"[{k}] activity: {acts[m.activity].dwa}\n    task: {acts[m.activity].task_text[:400]}\n"
            f"    course {m.course}, section {m.section}: “{m.quote}”\n    basis: {m.basis}"
            for k, m in enumerate(kept))
        res2 = complete(ADJUDICATE_SYSTEM, f"=== OCCUPATION: {occ_title} (SOC {soc}) ===\n\n{items}", ADJUDICATE_SCHEMA)
        if res2["data"] is not None:
            verdicts = {v["id"]: v for v in res2["data"]["verdicts"]}
            for k, m in enumerate(kept):
                v = verdicts.get(k)
                if v is not None:
                    m.kept, m.verdict = bool(v["keep"]), v.get("reason", "")
            for m in kept:
                if not m.kept:
                    dropped.append({"activity": m.activity + 1, "course": m.course, "section": m.section,
                                    "quote": m.quote, "basis": m.basis, "why": f"adjudicated: {m.verdict}"})
        else:
            logger.warning("adjudication failed (%s); keeping gated matches", res2["error"])
      except Exception as e:  # noqa: BLE001 — a failed second pass must not lose the first
        logger.warning("adjudication raised (%s); keeping gated matches", e)

    rows = [Row(a.dwa_id, a.dwa, a.task_text) for a in acts]
    for m in kept:
        if not m.kept:
            continue
        cell = rows[m.activity].cells.setdefault(m.course, Cell(0))
        if not any(_norm(e.quote) == _norm(m.quote) for e in cell.evidence):
            cell.evidence.append(Evidence(m.course, m.section, m.level, m.quote, m.basis))
        cell.level = max(cell.level, m.level)

    courses = []
    for c in program["courses"]:
        o = outlines[c["code"]]
        cur = None
        if coci_rows is not None:
            from ontology.coci import course_currency
            dept, num = c["code"].split(" ", 1)
            cc = course_currency(coci_rows, dept, num, o.approved or o.effective)
            cur = asdict(cc)
        courses.append({"code": c["code"], "title": o.title, "units": c.get("units"), "source_url": o.source_url,
                        "system": o.system, "effective": o.effective, "approved": o.approved, "sections": o.has(),
                        "notes": o.notes, "currency": cur})
    fmt = sorted({s for c in courses for s in c["sections"]}, key=list(LEVEL).index)
    note = (f"Read from {program['college']}'s course outlines of record ({outlines[program['courses'][0]['code']].system}); "
            f"sections present: {', '.join(SECTION_LABEL[s].lower() for s in fmt)}.")
    return Plate(program["college"], program["member_id"], program["certificate"], program.get("kind", "credit"),
                 program.get("top6"), program.get("top_name", ""), soc, occ_title, [], "", courses,
                 program.get("program_outcomes", []), rows, dropped, note, short_title=program.get("short_title", ""))


def _union_plate(new: Plate, old: Plate | None) -> Plate:
    """Carry every previously saved mark into the fresh plate (dedupe by quote)."""
    if old is None or old.paired_soc != new.paired_soc:
        return new
    old_rows = {r.dwa_id: r for r in old.rows}
    live = {c["code"] for c in new.courses}
    for r in new.rows:
        o = old_rows.get(r.dwa_id)
        if not o:
            continue
        for code, ocell in o.cells.items():
            if code != PLO and code not in live:        # a course dropped from the record takes its marks with it
                continue
            cell = r.cells.setdefault(code, Cell(0))
            have = {_norm(e.quote) for e in cell.evidence}
            for e in ocell.evidence:
                if _norm(e.quote) not in have:
                    cell.evidence.append(e)
                    have.add(_norm(e.quote))
            cell.level = max(cell.level, ocell.level)
    return new


def _candidates(row: Row) -> list[Evidence]:
    """Every course excerpt on a row (the certificate's own outcomes are not a course)."""
    return [e for code, cell in row.cells.items() if code != PLO for e in cell.evidence]


def _default_lead(row: Row, plate: Plate) -> dict | None:
    """The deterministic choice when no judgment is stored or the judge fails: tier, then
    the course's units, then catalog order, then the longer excerpt."""
    cands = _candidates(row)
    if not cands:
        return None
    units = {c["code"]: (c.get("units") or 0) for c in plate.courses}
    order = [c["code"] for c in plate.courses]
    e = max(cands, key=lambda e: (e.level, units.get(e.course, 0), -(order.index(e.course) if e.course in order else 99), len(e.quote)))
    return {"course": e.course, "section": e.section, "quote": e.quote, "reason": "default: tier, units, catalog order"}


def _lead_valid(row: Row) -> bool:
    """A stored lead still points at one of the row's excerpts."""
    ld = row.lead
    return bool(ld) and any(e.course == ld.get("course") and _norm(e.quote) == _norm(ld.get("quote", ""))
                            for e in _candidates(row))


def lead_for(row: Row, plate: Plate) -> dict | None:
    """The excerpt a page shows for a row: the stored judgment while it is still among the
    row's excerpts, else the deterministic default."""
    return row.lead if _lead_valid(row) else _default_lead(row, plate)


def rank_leads(plate: Plate, *, complete=None, rows: set[str] | None = None, force: bool = False) -> Plate:
    """Set the rows' leads. A stored lead that still points at one of the row's excerpts is
    KEPT (it is a mark, and may be a curator's) unless `force`; `rows` (dwa_ids) names the
    rows whose excerpts changed and so want judging again. Rows with one excerpt need no
    judgment; the rest go to the ranking pass in one call. Any failure keeps the defaults."""
    if complete is None:
        from llm.claude_cli import complete as _c
        complete = _c
    todo = []
    for r in plate.rows:
        keep = _lead_valid(r) and not force and (rows is None or r.dwa_id not in rows)
        if not keep:
            r.lead = _default_lead(r, plate)
            if len(_candidates(r)) > 1:
                todo.append(r)
    multi = [(i, r) for i, r in enumerate(plate.rows) if r in todo]
    if not multi:
        return plate
    ids: dict[tuple[int, int], Evidence] = {}
    blocks = []
    for i, r in multi:
        lines = [f"[{i}] activity: {r.dwa}\n    task: {r.task[:400]}"]
        for k, e in enumerate(_candidates(r)):
            ids[(i, k)] = e
            lines.append(f"    excerpt {k} — course {e.course}, section {SECTION_LABEL.get(e.section, e.section)}: “{e.quote}”")
        blocks.append("\n".join(lines))
    res = complete(RANK_SYSTEM, f"=== OCCUPATION: {plate.occupation} (SOC {plate.paired_soc}) ===\n\n" + "\n\n".join(blocks), RANK_SCHEMA)
    if res["data"] is None:
        logger.warning("ranking failed for %s vs %s (%s); default leads kept", plate.college, plate.paired_soc, res["error"])
        return plate
    for ch in (res["data"] or {}).get("choices", []):
        e = ids.get((int(ch["activity"]), int(ch["excerpt"])))
        if e is not None:
            plate.rows[int(ch["activity"])].lead = {"course": e.course, "section": e.section, "quote": e.quote, "reason": ch.get("reason", "")}
    return plate


def readings(program: dict) -> list[tuple[str, str]]:
    """The (soc, role) pairs a program is read against: its paired occupation, the play
    occupations its crosswalk reaches, and any review-only occupation (read, kept in the
    review file and the internal evidence tables, never drawn)."""
    out = [(program["paired_soc"], "paired")]
    for soc in program.get("reads_against", []):
        if soc != program["paired_soc"]:
            out.append((soc, "crosswalk"))
    for soc in program.get("review_socs", []):
        if soc not in {x[0] for x in out}:
            out.append((soc, "review"))
    return out


# ── the store: readings per program record ─────────────────────────────────────
def _plates_from_json(items: list[dict]) -> list[Plate]:
    plates = []
    for pl in items:
        rows = [Row(r["dwa_id"], r["dwa"], r["task"],
                    {k: Cell(v["level"], [Evidence(**e) for e in v["evidence"]]) for k, v in r["cells"].items()},
                    r.get("lead"))
                for r in pl["rows"]]
        plates.append(Plate(**{**{k: v for k, v in pl.items() if k != "rows"}, "rows": rows}))
    return plates


def load_readings(ref: str) -> dict[str, Plate]:
    """{soc -> Plate} saved for a program record; {} when it has never been read."""
    p = STORE / f"{ref}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {pl.paired_soc: pl for pl in _plates_from_json(d["plates"])}


def save_readings(ref: str, plates: dict[str, Plate], *, generated: str | None = None) -> tuple[Path, Path]:
    """Write a record's readings — the JSON the report renders, plus a Markdown review file
    listing every mark's quote and every drop, for the human pass. A plate carries no
    roster connection (role, pairing basis, crosswalk); `view_roster` supplies those."""
    STORE.mkdir(parents=True, exist_ok=True)
    stored = list(plates.values())
    d = {"program": ref, "generated": generated or date.today().isoformat(), "onet_vintage": ONET_VINTAGE,
         "plates": [asdict(pl) for pl in stored]}
    jp = STORE / f"{ref}.json"
    jp.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    md = [f"# Curriculum alignment review — {ref}", f"Generated {d['generated']} · {ONET_VINTAGE}", ""]
    for pl in stored:
        c = pl.counts()
        md += [f"## {pl.college} — {pl.certificate} → {pl.occupation} (SOC {pl.paired_soc})",
               f"{c['outcome_level']} of {c['activities']} activities at outcome level, {c['any_evidence']} with any evidence.", ""]
        for r in pl.rows:
            mark = "●" if r.level == 2 else "○" if r.level == 1 else "·"
            md.append(f"- {mark} **{r.dwa}**")
            for code, cell in r.cells.items():
                for e in cell.evidence:
                    md.append(f"    - {code} [{SECTION_LABEL[e.section]}]: “{e.quote}” — {e.basis}")
        if pl.dropped:
            md += ["", "### Dropped", ""]
            md += [f"- act {d_.get('activity')} · {d_.get('course')} · “{str(d_.get('quote', ''))[:90]}” — {d_.get('why')}" for d_ in pl.dropped]
        md.append("")
    rp = STORE / f"{ref}.review.md"
    rp.write_text("\n".join(md), encoding="utf-8")
    return jp, rp


def view_roster(roster_id: str) -> tuple[dict, list[Plate]]:
    """The roster and its plates: every (program, occupation) reading the roster asks for
    that has been saved, in roster-program then `readings()` order, each carrying the
    roster's connection (role, pairing basis, crosswalk) in place of the store's blanks."""
    roster = load_roster(roster_id)
    plates = []
    for p in roster_programs(roster):
        saved = load_readings(p["ref"])
        for soc, role in readings(p):
            pl = saved.get(soc)
            if pl is not None:
                plates.append(replace(pl, role=role, pairing_basis=p.get("pairing_basis", ""),
                                      crosswalk_socs=list(p.get("crosswalk_socs", []))))
    return roster, plates


# ── the run ────────────────────────────────────────────────────────────────────
def read_program(program: dict, socs: list[str], *, refresh: bool = False, adjudicate: bool = True,
                 coci_rows: list[dict] | None = None, accumulate: bool = True, new_only: bool = False,
                 complete=None, units: str = "all") -> dict[str, Plate]:
    """Read one resolved record (see `roster_programs`) against each SOC. With `accumulate`
    each fresh reading unions with the saved one; with `new_only` SOCs already saved are not
    re-read. Saved readings for other SOCs always ride along."""
    if units != "all" and not accumulate:
        raise ValueError("a partial re-read (units != 'all') must accumulate: without the union it would save a plate holding only that unit's marks")
    prev = load_readings(program["ref"])
    out = dict(prev)
    for soc in socs:
        if new_only and soc in prev:
            continue
        plate = align_program(program, soc=soc, refresh=refresh, adjudicate=adjudicate, coci_rows=coci_rows,
                              complete=complete, units=units)
        old = prev.get(soc)
        if units != "all" and old is not None:              # a partial re-read keeps the saved plate's course list
            plate = replace(plate, courses=old.courses, source_note=old.source_note, dropped=old.dropped + plate.dropped)
        merged = _union_plate(plate, old) if accumulate else plate
        if old is not None:                                  # carry the saved leads; re-judge only rows whose excerpts changed
            before = {r.dwa_id: {(e.course, _norm(e.quote)) for e in _candidates(r)} for r in old.rows}
            leads = {r.dwa_id: r.lead for r in old.rows}
            changed = set()
            for r in merged.rows:
                r.lead = leads.get(r.dwa_id)
                if {(e.course, _norm(e.quote)) for e in _candidates(r)} != before.get(r.dwa_id, set()):
                    changed.add(r.dwa_id)
            rank_leads(merged, complete=complete, rows=changed)
        else:
            rank_leads(merged, complete=complete)
        out[soc] = merged
    return out


def _check_against_def(roster: dict) -> None:
    """An evaluation roster shares its id with a report def; its occupations must come from
    that def's derived `socs` — one occupation list per document."""
    dp = SAVED / f"{roster['id']}.json"
    if not dp.exists():
        return
    d = json.loads(dp.read_text(encoding="utf-8"))
    if not d.get("socs"):
        return
    extra = [s for s in roster.get("occupations", []) if s not in d["socs"]]
    if extra:
        logger.warning("%s: roster occupations %s are not among the def's socs — add them to the def "
                       "(with a _comment) or drop them from the roster", roster["id"], ", ".join(extra))


def run(roster_id: str, *, refresh: bool = False, adjudicate: bool = True, coci: bool = False,
        only: str | None = None, accumulate: bool = True, new_only: bool = False, units: str = "all",
        rerank: bool = False) -> list[Plate]:
    """Read every program the roster cites against every occupation it connects it to, save
    each record's readings, and return the roster's view. `only` restricts the reading to
    one program (its college_key or ref); the others keep their saved readings. `rerank`
    makes no new reading: it re-judges each saved plate's lead excerpts and saves."""
    roster = load_roster(roster_id)
    _check_against_def(roster)
    coci_cache: dict[str, list[dict]] = {}
    for p in roster_programs(roster):
        if only and only not in (p["college_key"], p["ref"]):
            continue
        socs = [soc for soc, _ in readings(p)]
        if rerank:
            saved = load_readings(p["ref"])
            for soc in socs:
                if soc in saved:
                    rank_leads(saved[soc], force=True)
            save_readings(p["ref"], saved)
            continue
        if units != "all" and not p.get("program_outcomes"):
            continue
        if new_only and all(soc in load_readings(p["ref"]) for soc in socs):
            continue
        rows = None
        if coci:
            from ontology.coci import coci_code, fetch_course_export
            code = coci_code(p["college"])
            if code:
                rows = coci_cache.setdefault(code, fetch_course_export(code))
        plates = read_program(p, socs, refresh=refresh, adjudicate=adjudicate, coci_rows=rows,
                              accumulate=accumulate, new_only=new_only, units=units)
        save_readings(p["ref"], plates)
    return view_roster(roster_id)[1]


# ── scaffold: a draft record from COCI and the ProgramCourseFile ───────────────
#: The state's ProgramCourseFile (one CSV per college) is the award→course list; it is
#: read here only, at scaffold time, never bundled. `Program Control Number` is COCI's.
PCF_DIR = Path.home() / "Desktop" / "cc_dataset" / "programcoursefiles"
_TIER_LABEL = {"certificate": "Certificate of Achievement", "associate degree": "Associate Degree",
               "transfer degree": "Associate Degree for Transfer", "baccalaureate": "Bachelor's Degree",
               "noncredit award": "Certificate of Completion"}


def _pcf_code(course_id: str, *, keep_zeros: bool = False) -> str:
    """'ENGR061A' → 'ENGR 61A': a space before the first digit, leading zeros dropped.
    `keep_zeros` for colleges that write 'MTT 020'. C-ID style ids ('COMMC1000') come out
    wrong ('COMMC 1000') and are for the human pass."""
    m = re.match(r"^([A-Za-z]+)\s*(\d+)(.*)$", course_id.strip())
    if not m:
        return course_id.strip()
    dept, num, tail = m.groups()
    if not keep_zeros:
        num = num.lstrip("0") or "0"
    return f"{dept.upper()} {num}{tail.strip().upper()}"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def scaffold_record(award: "CociAward", pcf_rows: list[dict], *, college: str, college_key: str, source: dict | None,
                    keep_zeros: bool = False, top_name: str = "") -> dict:
    """A draft program record: identity from the COCI award, courses from the award's Active
    ProgramCourseFile rows. A DRAFT, never read as-is — the file lists every course the
    award can count, general-education and "or" alternatives included, and misses support
    courses; a human trims and confirms what `_todo` lists."""
    seen, courses = set(), []
    for r in pcf_rows:
        if (r.get("Course Status") or "").strip() != "Active":
            continue
        code = _pcf_code(r["Course Id"], keep_zeros=keep_zeros)
        if code in seen:
            continue
        seen.add(code)
        courses.append({"code": code, "title": (r.get("Course Title") or "").strip().title(), "units": None})
    label = _TIER_LABEL.get(award.tier, award.tier.title())
    return {
        "_todo": ["trim courses to the certificate's own requirements (PCF lists GE and 'or' alternatives; misses support courses)",
                  "confirm each course code's spelling against the college's outline system (it is the key)",
                  "paste the certificate's program outcomes and description from the catalog",
                  "confirm `source` (the outline adapter) and add `course_sources` overrides where a course lives elsewhere"],
        "college": college, "college_key": college_key, "member_id": college_key,
        "certificate": f"{label}, {award.title}", "short_title": award.title, "kind": "noncredit" if award.tier == "noncredit award" else "credit",
        "control_number": award.control_number, "award": award.award, "status": award.status,
        "top6": award.top6, "top_name": top_name,
        "source": source or {"system": "TODO"}, "course_sources": {},
        "program_description": "", "program_outcomes": [], "courses": courses}


def scaffold(college_key: str, control_number: str, *, pcf_dir: Path = PCF_DIR, keep_zeros: bool = False,
             out: Path | None = None) -> Path:
    """Write a draft record for the COCI award `control_number` at the college with catalog
    key `college_key`. Refuses to overwrite an existing record unless `out` says where."""
    import csv
    from ontology.coci import award_by_control
    from ontology.crosswalks import load_top_titles
    from partnerships.members import _catalog
    keys = {rec["key"]: name for name, rec in _catalog().items()}
    siblings = sorted(PROGRAMS.glob(f"{college_key}-*.json"))
    college = keys.get(college_key) or (json.loads(siblings[0].read_text())["college"] if siblings else None)
    if college is None:
        raise SystemExit(f"unknown college key {college_key!r}")
    award = award_by_control(college, control_number)
    if award is None:
        raise SystemExit(f"no COCI award with control number {control_number} at {college}")
    catalog_key = next((k for k, n in keys.items() if n == college), college_key)
    pcf = next((pcf_dir / f"ProgramCourseFile_{k}.csv" for k in dict.fromkeys([college_key, catalog_key])
                if (pcf_dir / f"ProgramCourseFile_{k}.csv").exists()), None)
    if pcf is None:
        raise SystemExit(f"no ProgramCourseFile for {college_key!r} in {pcf_dir}")
    with pcf.open(encoding="cp1252", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)
                if (r.get("Program Control Number") or "").lstrip("0") == control_number.lstrip("0")]
    source = json.loads(siblings[0].read_text()).get("source") if siblings else None
    rec = scaffold_record(award, rows, college=college, college_key=college_key, source=source, keep_zeros=keep_zeros,
                          top_name=load_top_titles().get(award.top6, ""))
    path = out or PROGRAMS / f"{college_key}-{_slug(award.title)}.json"
    if out is None and path.exists():
        raise SystemExit(f"{path} exists; pass --out to write the draft elsewhere")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Curriculum alignment: read a roster's programs against its occupations, or scaffold a program record.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="read each roster program's outlines against the occupations the roster connects it to")
    r.add_argument("roster", help="roster id, e.g. svamp-manufacturing-technician (an evaluation's roster shares its def slug)")
    r.add_argument("--refresh", action="store_true", help="re-fetch outlines from the college systems")
    r.add_argument("--no-adjudicate", action="store_true")
    r.add_argument("--coci", action="store_true", help="check each outline's currency against the COCI course export")
    r.add_argument("--only", help="one program (college_key or record ref); the others keep their saved readings")
    r.add_argument("--fresh", action="store_true", help="do not union a fresh reading with the saved one")
    r.add_argument("--new-only", action="store_true", help="read only (program, occupation) pairs the store lacks")
    r.add_argument("--units", choices=("all", "plo"), default="all", help="plo: re-read only the certificate's program outcomes, unioned into the saved plates")
    r.add_argument("--rerank", action="store_true", help="no new reading: re-judge each saved plate's lead excerpt per activity and save")
    sc = sub.add_parser("scaffold", help="draft a program record from COCI and the ProgramCourseFile")
    sc.add_argument("college_key", help="catalog key, e.g. foothill")
    sc.add_argument("control_number", help="the award's COCI control number, e.g. 43983")
    sc.add_argument("--pcf-dir", type=Path, default=PCF_DIR)
    sc.add_argument("--keep-zeros", action="store_true", help="keep leading zeros in course numbers (MTT 020)")
    sc.add_argument("--out", type=Path, help="write the draft here instead of data/programs/")
    a = ap.parse_args()
    if a.cmd == "run" and a.fresh and a.units != "all":
        ap.error("--fresh cannot be combined with --units plo: a partial re-read must union with the saved plate")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if a.cmd == "scaffold":
        print(f"wrote {scaffold(a.college_key, a.control_number, pcf_dir=a.pcf_dir, keep_zeros=a.keep_zeros, out=a.out)}")
    else:
        plates = run(a.roster, refresh=a.refresh, adjudicate=not a.no_adjudicate, coci=a.coci, only=a.only,
                     accumulate=not a.fresh, new_only=a.new_only, units=a.units, rerank=a.rerank)
        for pl in plates:
            c = pl.counts()
            print(f"{pl.college:26s} vs {pl.paired_soc} ({pl.role:9s}): {c['outcome_level']:2d} outcome-level, {c['any_evidence']:2d} any, of {c['activities']} | dropped {len(pl.dropped)}")
        print(f"readings in {STORE}")
