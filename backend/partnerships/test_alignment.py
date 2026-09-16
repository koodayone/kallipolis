"""Unit tests for partnerships.alignment and alignment_plate — the gate, the roster plumbing, and the plate.

The gate is the rule that keeps the LLM matcher honest: fail-closed on the verbatim quote,
level set by the section the quote is actually found in. No LLM call is made here.

Coverage:
  - the gate keeps verbatim quotes, relabels a quote to the section it is found in, resolves course codes with or without spaces, and drops paraphrases and unknown courses
  - the gate is case- and punctuation-insensitive but never fuzzy
  - the SVAMP roster's five programs all have every course's outline in the cache with outcomes and a source URL
  - the plate renders program-outcome and course columns, marks gaps, and its readout and evidence table carry the counts and quotes
  - an occupation block lists up to N evidenced activities in derived-importance order with colour-coded course chips (one style), leaves unevidenced rows out unless show_gaps, and ignores program-outcome cells
  - a cell shows at most three courses, strongest evidence first, with a +N chip for the rest
"""

from courses.outlines import Outline
from partnerships.alignment import PLO, Cell, Evidence, Plate, Row, gate, load_roster, program_outlines
from partnerships.alignment_plate import evidence_table, occupation_block, plate_readout, plate_svg


def _outline():
    return Outline("Mission College", "elumen", "MTT 020", "PLC Process Control Systems",
                   "This course covers Programmable Logic Controller (PLC) systems and troubleshooting.",
                   outcomes=["Implement and troubleshoot a basic functional control system using ladder-logic programming"],
                   objectives=["Design a PLC program using ladder-logic or function block diagramming"],
                   content=["Ladder logic programming", "Timers, counters, and comparison functions"],
                   lab=["Build and test a basic ladder logic circuit"], assignments=[])


PROGRAM = {"college": "Mission College", "program_outcomes": ["Troubleshoot and repair electrical, electronic, and mechanical systems"]}


def test_gate_keeps_verbatim_quotes_and_sets_level_by_found_section():
    o = {"MTT 020": _outline()}
    raw = [
        # literal section, verbatim → solid
        {"activity": 1, "course": "MTT 020", "section": "outcomes",
         "quote": "troubleshoot a basic functional control system using ladder-logic programming", "basis": "x"},
        # claimed as an outcome but the words live in LAB → relabelled and demoted to a ring
        {"activity": 2, "course": "MTT 020", "section": "outcomes", "quote": "Build and test a basic ladder logic circuit", "basis": "x"},
        # program outcomes pseudo-course
        {"activity": 3, "course": "PLO", "section": "program_outcomes", "quote": "Troubleshoot and repair electrical, electronic, and mechanical systems", "basis": "x"},
        # paraphrase, not verbatim → dropped
        {"activity": 1, "course": "MTT 020", "section": "outcomes", "quote": "students troubleshoot PLC control systems", "basis": "x"},
        # unknown course → dropped
        {"activity": 1, "course": "MTT 999", "section": "content", "quote": "Ladder logic programming", "basis": "x"},
        # course code spelled without the space still resolves
        {"activity": 4, "course": "MTT020", "section": "content", "quote": "Timers, counters, and comparison functions", "basis": "x"},
    ]
    kept, dropped = gate(raw, PROGRAM, o, n_activities=5)
    assert [(m.activity, m.course, m.section, m.level) for m in kept] == [
        (0, "MTT 020", "outcomes", 2), (1, "MTT 020", "lab", 1), (2, PLO, "program_outcomes", 2), (3, "MTT 020", "content", 1)]
    assert [d["why"] for d in dropped] == ["quote not verbatim in that course", "unknown course 'MTT 999'"]


def test_gate_is_case_and_punctuation_insensitive_but_not_fuzzy():
    o = {"MTT 020": _outline()}
    ok = [{"activity": 1, "course": "MTT 020", "section": "objectives", "quote": "design a plc program using ladder logic", "basis": ""}]
    kept, dropped = gate(ok, PROGRAM, o, 1)
    assert kept and kept[0].section == "objectives"
    bad = [{"activity": 1, "course": "MTT 020", "section": "objectives", "quote": "design a PLC program in ladder logic", "basis": ""}]
    kept, dropped = gate(bad, PROGRAM, o, 1)
    assert not kept and dropped


def test_roster_and_cached_outlines_cover_every_course():
    roster = load_roster("svamp-manufacturing-technician")
    assert len(roster["programs"]) == 5
    for p in roster["programs"]:
        outlines = program_outlines(p)              # cache only — no network in tests
        assert set(outlines) == {c["code"] for c in p["courses"]}
        for o in outlines.values():
            assert o.source_url.startswith("https://")
            assert o.outcomes, f"{p['college']} {o.code} has no outcomes in its outline"


def test_plate_renders_marks_gaps_and_evidence():
    rows = [Row("d1", "Diagnose equipment malfunctions.", "task",
                {"MTT 020": Cell(2, [Evidence("MTT 020", "outcomes", 2, "troubleshoot a basic functional control system", "b")])}),
            Row("d2", "Clean workpieces or finished products.", "task", {})]
    pl = Plate("Mission College", "mission", "Certificate of Achievement, Mechatronic Technology", "credit", "0935.00",
               "Electro-Mechanical Technology", "17-3024", "Electro-Mechanical and Mechatronics Technologists and Technicians",
               ["17-3024", "51-9141"], "stated purpose",
               [{"code": "MTT 020", "title": "PLC", "units": 2, "source_url": "https://x", "system": "elumen",
                 "effective": "2026FA", "approved": "2025-10-29", "sections": ["outcomes"], "notes": "", "currency": None}],
               ["Troubleshoot and repair"], rows)
    svg = plate_svg(pl)
    assert svg.startswith("<svg") and "Program outcomes" in svg and "MTT 020" in svg and ">gap<" in svg
    assert pl.counts() == {"activities": 2, "outcome_level": 1, "any_evidence": 1, "per_course": {"MTT 020": 1}}
    assert "1 of 2" in plate_readout(pl) and "Clean workpieces" in plate_readout(pl)
    assert "troubleshoot a basic functional control system" in evidence_table(pl)


def test_occupation_block_lists_chips_and_gaps_and_skips_program_outcomes():
    rows = [Row("d1", "Diagnose equipment malfunctions.", "t",
                {"MTT 020": Cell(2, [Evidence("MTT 020", "outcomes", 2, "q1", "b")]),
                 PLO: Cell(2, [Evidence(PLO, "program_outcomes", 2, "q2", "b")])}),
            Row("d2", "Clean workpieces or finished products.", "t", {}),
            Row("d3", "Inspect production equipment.", "t", {"MTT 012": Cell(1, [Evidence("MTT 012", "lab", 1, "q3", "b")])})]
    mk = lambda college, mid, role: Plate(college, mid, "Cert", "credit", "0935.00", "EMT", "17-3024", "Mechatronics Techs",
                                          ["17-3024"], "", [{"code": "MTT 020"}, {"code": "MTT 012"}], [], rows, role=role)
    html = occupation_block("17-3024", [mk("Mission College", "mission", "paired")], top_n=2)
    assert 'class="chip"' in html and "MTT 020" in html and "chip solid" not in html and "chip ring" not in html
    # unevidenced d2 is left out and the next evidenced activity (d3) fills the second slot
    assert "Clean workpieces" not in html and "Inspect production equipment" in html
    assert "no course in the consortium evidences this" not in html
    assert "Program outcomes" not in html and "PLO" not in html           # PLO cells are not chips
    assert "<b>2 course marks</b>" in html
    # internal review: show_gaps keeps the ranked rows, empty ones annotated
    g = occupation_block("17-3024", [mk("Mission College", "mission", "paired")], top_n=2, show_gaps=True)
    assert "Clean workpieces" in g and "no course in the consortium evidences this" in g and "<b>1 of 2</b>" in g


def test_cell_caps_chips_at_three_strongest_first_with_overflow():
    cells = {f"C {i}": Cell(1 if i < 4 else 2, [Evidence(f"C {i}", "content" if i < 4 else "outcomes", 1 if i < 4 else 2, f"q{i}", "b")]) for i in range(5)}
    rows = [Row("d1", "Act.", "t", cells)]
    pl = Plate("Mission College", "mission", "Cert", "credit", "0935.00", "EMT", "17-3024", "Mechatronics Techs", [], "",
               [{"code": f"C {i}"} for i in range(5)], [], rows)
    html = occupation_block("17-3024", [pl], top_n=1)
    assert html.count('class="chip"') == 3 and 'class="chip alg-more"' in html and ">+2<" in html
    assert html.index("C 4") < html.index("C 0")        # the outcome-level course leads
