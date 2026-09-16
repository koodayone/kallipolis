"""Curriculum alignment — which courses carry the work of the target occupation.

One program per college, paired with ONE target occupation, read from its course
outlines of record against the occupation's core work activities. The output is a plate
per program: activities down the side (O*NET's order), the program's courses across the
top, and a mark wherever a course's outline evidences an activity — solid where an
outcome or objective states it, a ring where the description, content, lab or
assignments involve it. Every mark carries the sentence it rests on.

THE EDITORIAL RULES (locked 2026-09-16; change them here, not in prose):

  unit        the O*NET detailed work activity; rows = activities anchored to the
              occupation's Core tasks, in O*NET's importance order, no numbers shown
  pairing     CHOSEN from the program's stated purpose (roster `paired_soc`); the
              TOP→CIP→SOC crosswalk's verdict is shown beside it, never used to choose
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
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from courses.outlines import Outline, retrieve
from occupations.descriptions import get_title
from occupations.work_activities import ONET_VINTAGE, WorkActivity, get_work_activities

logger = logging.getLogger(__name__)

DATA = Path(__file__).parent / "data"
SAVED = Path(__file__).parent / "saved_reports"

LEVEL = {"outcomes": 2, "objectives": 2, "program_outcomes": 2,
         "description": 1, "content": 1, "lab": 1, "assignments": 1}
SECTION_LABEL = {"outcomes": "SLO", "objectives": "Objective", "program_outcomes": "Program outcome",
                 "description": "Description", "content": "Content outline", "lab": "Lab content",
                 "assignments": "Assignment"}
PLO = "PLO"   # the pseudo-course for the certificate's own outcomes


# ── roster ─────────────────────────────────────────────────────────────────────
def load_roster(roster_id: str) -> dict:
    p = DATA / f"{roster_id.replace('-', '_')}.json"
    return json.loads(p.read_text(encoding="utf-8"))


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
        if course.upper().startswith(PLO):
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

    @property
    def level(self) -> int:
        return max((c.level for c in self.cells.values()), default=0)


@dataclass
class Plate:
    college: str
    member_id: str
    certificate: str
    kind: str
    top: str | None
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
    role: str = "paired"        # paired | crosswalk | appendix — how the program connects to this occupation

    def counts(self) -> dict:
        n = len(self.rows)
        return {"activities": n,
                "outcome_level": sum(1 for r in self.rows if r.level == 2),
                "any_evidence": sum(1 for r in self.rows if r.level >= 1),
                "per_course": {c["code"]: sum(1 for r in self.rows if c["code"] in r.cells) for c in self.courses}}


@dataclass
class Alignment:
    roster_id: str
    generated: str
    onet_vintage: str
    plates: list[Plate]


# ── the run ────────────────────────────────────────────────────────────────────
def align_program(program: dict, *, soc: str | None = None, refresh: bool = False,
                  adjudicate: bool = True, complete=None, coci_rows: list[dict] | None = None,
                  role: str = "paired") -> Plate:
    """Read one program against one occupation. `complete` is the LLM seam
    (llm.claude_cli.complete by default); `coci_rows` the college's COCI course export
    if a currency check is wanted."""
    if complete is None:
        from llm.claude_cli import complete as _c
        complete = _c
    soc = soc or program["paired_soc"]
    acts = get_work_activities(soc)
    occ_title = get_title(soc) or soc
    outlines = program_outlines(program, refresh=refresh)

    acts_text = _activities_text(occ_title, soc, acts)
    # Two proposers, one gate. A whole program in one prompt under-proposes for large
    # programs (Mission's twelve outlines in one call drew 21 proposals; course by
    # course they drew 81) while a lone course loses the certificate's framing (Foothill
    # drew 23 as a program and 10 course by course). Their union is what the gate and
    # the adjudicator then discipline. The certificate's own outcomes get a call too.
    units: list[tuple[str, str]] = [("program", _program_text(program, outlines))]
    if program.get("program_outcomes"):
        units.append((PLO, f"CERTIFICATE: {program['certificate']} ({program['college']})\n" +
                      "\n".join(f"PLO: {x}" for x in program["program_outcomes"])))
    for c in program["courses"]:
        units.append((c["code"], _program_text({**program, "courses": [c], "program_outcomes": []}, outlines)))

    def _match(unit):
        code, text = unit
        r = complete(MATCH_SYSTEM, f"{acts_text}\n\n=== PROGRAM TEXT ({code}) ===\n{text}", MATCH_SCHEMA)
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
                 program.get("top"), program.get("top_name", ""), soc, occ_title, program.get("crosswalk_socs", []),
                 program.get("pairing_basis", ""), courses, program.get("program_outcomes", []), rows, dropped, note, role)


def _union_plate(new: Plate, old: Plate | None) -> Plate:
    """Carry every previously saved mark into the fresh plate (dedupe by quote)."""
    if old is None or old.paired_soc != new.paired_soc:
        return new
    old_rows = {r.dwa_id: r for r in old.rows}
    for r in new.rows:
        o = old_rows.get(r.dwa_id)
        if not o:
            continue
        for code, ocell in o.cells.items():
            cell = r.cells.setdefault(code, Cell(0))
            have = {_norm(e.quote) for e in cell.evidence}
            for e in ocell.evidence:
                if _norm(e.quote) not in have:
                    cell.evidence.append(e)
                    have.add(_norm(e.quote))
            cell.level = max(cell.level, ocell.level)
    return new


def readings(program: dict) -> list[tuple[str, str]]:
    """The (soc, role) pairs a program is read against: its paired occupation, the play
    occupations its crosswalk reaches, and any appendix-only occupation."""
    out = [(program["paired_soc"], "paired")]
    for soc in program.get("reads_against", []):
        if soc != program["paired_soc"]:
            out.append((soc, "crosswalk"))
    for soc in program.get("appendix_socs", []):
        if soc not in {x[0] for x in out}:
            out.append((soc, "appendix"))
    return out


def run(roster_id: str, *, refresh: bool = False, adjudicate: bool = True, coci: bool = False,
        only: str | None = None, accumulate: bool = True, new_only: bool = False) -> Alignment:
    roster = load_roster(roster_id)
    previous = load_alignment(roster_id) if (accumulate or only or new_only) else None
    prev = {(p.college, p.paired_soc): p for p in previous.plates} if previous else {}
    coci_cache: dict[str, list[dict]] = {}
    plates = []
    for p in roster["programs"]:
        rows = None
        for soc, role in readings(p):
            key = (p["college"], soc)
            if (only and p["college_key"] != only) or (new_only and key in prev):
                if key in prev:                       # untouched readings ride along
                    plates.append(prev[key])
                continue
            if coci and rows is None:
                from ontology.coci import fetch_course_export, _COLLEGE_CODE
                code = _COLLEGE_CODE.get(p["college"])
                if code:
                    rows = coci_cache.setdefault(code, fetch_course_export(code))
            plate = align_program(p, soc=soc, refresh=refresh, adjudicate=adjudicate, coci_rows=rows, role=role)
            if accumulate:
                plate = _union_plate(plate, prev.get(key))
            plates.append(plate)
    return Alignment(roster_id, date.today().isoformat(), ONET_VINTAGE, plates)


def save(al: Alignment) -> tuple[Path, Path]:
    """The alignment JSON the report renders, plus a Markdown review file listing every
    mark's quote and every drop, for the human pass."""
    SAVED.mkdir(exist_ok=True)
    jp = SAVED / f"{al.roster_id}.alignment.json"
    jp.write_text(json.dumps(asdict(al), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    md = [f"# Curriculum alignment review — {al.roster_id}", f"Generated {al.generated} · {al.onet_vintage}", ""]
    for pl in al.plates:
        c = pl.counts()
        md += [f"## {pl.college} — {pl.certificate} → {pl.occupation} ({pl.role})",
               f"Read against {pl.occupation} (SOC {pl.paired_soc}), connected by {pl.role}. {pl.pairing_basis if pl.role == 'paired' else ''}",
               f"{c['outcome_level']} of {c['activities']} activities at outcome level, {c['any_evidence']} with any evidence.", ""]
        for r in pl.rows:
            mark = "●" if r.level == 2 else "○" if r.level == 1 else "·"
            md.append(f"- {mark} **{r.dwa}**")
            for code, cell in r.cells.items():
                for e in cell.evidence:
                    md.append(f"    - {code} [{SECTION_LABEL[e.section]}]: “{e.quote}” — {e.basis}")
        if pl.dropped:
            md += ["", "### Dropped", ""]
            md += [f"- act {d.get('activity')} · {d.get('course')} · “{str(d.get('quote', ''))[:90]}” — {d.get('why')}" for d in pl.dropped]
        md.append("")
    rp = SAVED / f"{al.roster_id}.alignment.review.md"
    rp.write_text("\n".join(md), encoding="utf-8")
    return jp, rp


def load_alignment(roster_id: str) -> Alignment | None:
    p = SAVED / f"{roster_id}.alignment.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    plates = []
    for pl in d["plates"]:
        rows = [Row(r["dwa_id"], r["dwa"], r["task"],
                    {k: Cell(v["level"], [Evidence(**e) for e in v["evidence"]]) for k, v in r["cells"].items()})
                for r in pl["rows"]]
        plates.append(Plate(**{**{k: v for k, v in pl.items() if k != "rows"}, "rows": rows}))
    return Alignment(d["roster_id"], d["generated"], d["onet_vintage"], plates)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Read each roster program's outlines against its paired occupation.")
    ap.add_argument("roster", help="roster id, e.g. svamp-manufacturing-technician")
    ap.add_argument("--refresh", action="store_true", help="re-fetch outlines from the college systems")
    ap.add_argument("--no-adjudicate", action="store_true")
    ap.add_argument("--coci", action="store_true", help="check each outline's currency against the COCI course export")
    ap.add_argument("--only", help="one college_key (other plates are carried over from the saved alignment)")
    ap.add_argument("--fresh", action="store_true", help="do not union with the saved alignment")
    ap.add_argument("--new-only", action="store_true", help="compute only (program, occupation) readings the saved alignment lacks")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    al = run(a.roster, refresh=a.refresh, adjudicate=not a.no_adjudicate, coci=a.coci, only=a.only, accumulate=not a.fresh, new_only=a.new_only)
    jp, rp = save(al)
    for pl in al.plates:
        c = pl.counts()
        print(f"{pl.college:26s} vs {pl.paired_soc} ({pl.role:9s}): {c['outcome_level']:2d} outcome-level, {c['any_evidence']:2d} any, of {c['activities']} | dropped {len(pl.dropped)}")
    print(f"wrote {jp}\n      {rp}")
