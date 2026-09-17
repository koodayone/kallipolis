"""Unit tests for partnerships.alignment and alignment_plate — the gate, records and rosters, the store, and the plate.

The gate is the rule that keeps the LLM matcher honest: fail-closed on the verbatim quote,
level set by the section the quote is actually found in. No LLM call is made here; the
reading tests stub the LLM seam and the store.

Coverage:
  - the gate keeps verbatim quotes, relabels a quote to the section it is found in, resolves course codes with or without spaces, and drops paraphrases and unknown courses
  - the gate is case- and punctuation-insensitive but never fuzzy
  - the SVAMP roster's five entries resolve to program records, and every course's outline is in the cache with outcomes and a source URL
  - the saved per-program stores hold every (program, occupation) reading the SVAMP roster asks for
  - view_roster sets role, pairing basis and crosswalk from the roster, not the store, in roster order
  - read_program unions a fresh reading with the saved one and leaves other saved occupations in place
  - a program-outcomes-only re-read keeps the saved plate's courses and adds PLO cells; the gate takes the certificate's name as PLO
  - a certificate column shows one mark per activity — the lead excerpt with its course title and outline-section caption; program outcomes are not drawn
  - rank_leads asks one judgment for rows with several excerpts, stores the choice, and falls back to tier, units, catalog order
  - a block takes an intro (the occupation description and its key) under its title; the certificate key names the chip, no swatch
  - an occupation block and legend label columns by certificate when the roster asks, and by college otherwise
  - a ProgramCourseFile course id becomes the college's spelling (space before the number, zeros dropped or kept)
  - scaffold_record drafts a record from a COCI award and Active PCF rows, with a _todo list and the source it is given; a noncredit award is a certificate of completion
  - rank_leads maps the judge's choices by row index across several multi-excerpt rows and ignores out-of-range ones
  - a saved reading round-trips through the store with its leads, and carries no roster connection
  - a course dropped from a record takes its marks with it on the next union
  - a stored lead survives a re-read while its excerpt does; only rows whose excerpts changed are re-judged
  - a partial re-read refuses to run without accumulation
  - an occupation block lists up to N evidenced activities in derived-importance order with colour-coded course chips (one style) that link to the course's outline of record, leaves unevidenced rows out unless show_gaps, and ignores program-outcome cells
  - a cell shows at most three courses, strongest evidence first, with a +N chip for the rest
"""

import json

from courses.outlines import Outline
from ontology.coci import CociAward
from partnerships import alignment as A
from partnerships.alignment import (PLO, Cell, Evidence, Plate, Row, _pcf_code, _union_plate, gate, lead_for, load_readings,
                                    load_roster, program_outlines, read_program, readings, roster_programs, save_readings,
                                    scaffold_record, view_roster)
from partnerships.alignment_plate import column_legend, occupation_block


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
    programs = roster_programs(roster)
    assert len(programs) == 5 and roster["columns"] == "college"
    for p in programs:
        assert p["ref"] == p["program"] and p["control_number"] and len(p["top6"]) == 6 and p["short_title"]
        outlines = program_outlines(p)              # cache only — no network in tests
        assert set(outlines) == {c["code"] for c in p["courses"]}
        for o in outlines.values():
            assert o.source_url.startswith("https://")
            assert o.outcomes, f"{p['college']} {o.code} has no outcomes in its outline"


def test_stores_cover_every_reading_the_roster_asks_for():
    roster = load_roster("svamp-manufacturing-technician")
    for p in roster_programs(roster):
        saved = load_readings(p["ref"])
        assert {soc for soc, _ in readings(p)} <= set(saved), p["ref"]
        for soc, pl in saved.items():
            assert pl.paired_soc == soc and pl.role == "" and pl.top6 == p["top6"] and pl.short_title == p["short_title"]


def _plate(college, mid, soc, cert="Cert", **kw):
    rows = [Row("d1", "Diagnose equipment malfunctions.", "t", {"C 1": Cell(1, [Evidence("C 1", "content", 1, "q", "b")])})]
    return Plate(college, mid, cert, "credit", "095600", "Mfg", soc, "Occ", kw.pop("crosswalk_socs", []), kw.pop("pairing_basis", ""),
                 [{"code": "C 1"}], [], rows, **kw)


def test_view_roster_takes_connection_from_the_roster_in_roster_order(monkeypatch):
    roster = {"id": "r", "columns": "college", "occupations": ["17-3024", "17-3026"], "top_n": 10,
              "programs": [{"program": "b-x", "paired_soc": "17-3026", "crosswalk_socs": ["17-3024"], "pairing_basis": "stated",
                            "reads_against": ["17-3024"], "review_socs": ["51-4041"]},
                           {"program": "a-y", "paired_soc": "17-3024", "reads_against": []}]}
    monkeypatch.setattr(A, "load_roster", lambda _id: roster)
    monkeypatch.setattr(A, "load_program", lambda ref: {"college": ref.upper(), "college_key": ref[0], "member_id": ref[0]})
    store = {"b-x": {s: _plate("B", "b", s) for s in ("17-3026", "17-3024", "51-4041")},
             "a-y": {"17-3024": _plate("A", "a", "17-3024"), "99-9999": _plate("A", "a", "99-9999")}}
    monkeypatch.setattr(A, "load_readings", lambda ref: store[ref])
    _, plates = view_roster("r")
    assert [(p.member_id, p.paired_soc, p.role) for p in plates] == [
        ("b", "17-3026", "paired"), ("b", "17-3024", "crosswalk"), ("b", "51-4041", "review"), ("a", "17-3024", "paired")]
    assert plates[0].pairing_basis == "stated" and plates[0].crosswalk_socs == ["17-3024"]
    assert plates[3].pairing_basis == "" and plates[3].crosswalk_socs == []     # a reading the roster does not ask for is left out


def test_read_program_unions_with_the_store_and_keeps_other_occupations(monkeypatch):
    prev = _plate("Mission College", "mission", "17-3024")
    other = _plate("Mission College", "mission", "51-9141")
    monkeypatch.setattr(A, "load_readings", lambda ref: {"17-3024": prev, "51-9141": other})
    monkeypatch.setattr(A, "program_outlines", lambda program, refresh=False: {"MTT 020": _outline(), "C 1": _outline()})
    monkeypatch.setattr(A, "get_work_activities", lambda soc: [type("W", (), {"dwa_id": "d1", "dwa": "Diagnose equipment malfunctions.", "task_text": "t"})()])
    monkeypatch.setattr(A, "get_title", lambda soc: "Occ")
    program = {"ref": "mission-mechatronic-technology", "college": "Mission College", "member_id": "mission", "college_key": "mission",
               "certificate": "Cert", "courses": [{"code": "MTT 020"}], "program_outcomes": [], "source": {}}
    fresh = lambda system, user, schema: {"data": {"matches": [
        {"activity": 1, "course": "MTT 020", "section": "content", "quote": "Ladder logic programming", "basis": "b"}], "choices": []}, "error": None}
    prev.rows[0].lead = {"course": "C 1", "section": "content", "quote": "q", "reason": "curator"}
    program["courses"] = [{"code": "MTT 020"}, {"code": "C 1"}]                # both courses still on the record
    out = read_program(program, ["17-3024"], adjudicate=False, complete=fresh)
    assert set(out) == {"17-3024", "51-9141"} and out["51-9141"] is other
    quotes = {e.quote for e in out["17-3024"].rows[0].cells["MTT 020"].evidence} | {e.quote for e in out["17-3024"].rows[0].cells["C 1"].evidence}
    assert quotes == {"Ladder logic programming", "q"}                        # the saved mark survives the re-read
    assert out["17-3024"].rows[0].lead["reason"] == "curator" or out["17-3024"].rows[0].lead["course"] in ("C 1", "MTT 020")
    out = read_program(program, ["17-3024"], adjudicate=False, complete=fresh, new_only=True)
    assert out["17-3024"] is prev                                              # already saved: not re-read


def test_plo_only_reread_unions_into_the_saved_plate(monkeypatch):
    prev = _plate("Mission College", "mission", "17-3024")
    monkeypatch.setattr(A, "load_readings", lambda ref: {"17-3024": prev})
    monkeypatch.setattr(A, "program_outlines", lambda program, refresh=False: {"MTT 020": _outline(), "C 1": _outline()})
    monkeypatch.setattr(A, "get_work_activities", lambda soc: [type("W", (), {"dwa_id": "d1", "dwa": "Diagnose equipment malfunctions.", "task_text": "t"})()])
    monkeypatch.setattr(A, "get_title", lambda soc: "Occ")
    program = {"ref": "mission-mechatronic-technology", "college": "Mission College", "member_id": "mission", "college_key": "mission",
               "certificate": "Certificate of Achievement, Mechatronic Technology", "courses": [{"code": "MTT 020"}], "source": {},
               "program_outcomes": ["Troubleshoot and repair electrical, electronic, and mechanical systems and devices."]}
    calls = []
    def fake(system, user, schema):
        calls.append(user)
        return {"data": {"matches": [{"activity": 1, "course": "Certificate of Achievement, Mechatronic Technology",
                                      "section": "program_outcomes", "quote": "Troubleshoot and repair electrical, electronic, and mechanical systems", "basis": "b"}],
                         "choices": []}, "error": None}
    out = read_program(program, ["17-3024"], adjudicate=False, complete=fake, units="plo")
    assert "PROGRAM OUTCOMES (PLO)" in calls[0] and not any("PROGRAM TEXT" in c for c in calls)   # the outcomes unit alone (plus the ranking pass)
    row = out["17-3024"].rows[0]
    assert PLO in row.cells and row.cells[PLO].level == 2                    # certificate-named course gated as PLO
    assert "C 1" in row.cells and out["17-3024"].courses == prev.courses     # the saved course marks and course list survive


def test_columns_label_by_certificate_or_college():
    plates = [_plate("Foothill College", "foothill", "17-3024", cert="Certificate of Achievement, Semiconductor Processing Technician",
                     short_title="Semiconductor Processing"),
              _plate("Foothill College", "foothill", "17-3024", cert="Certificate of Achievement, Vacuum Technology", short_title="Vacuum Technology")]
    by_cert = occupation_block("17-3024", plates, columns="certificate")
    assert by_cert.count("alg-colhd") == 2 and "Semiconductor Processing<" in by_cert and "Vacuum Technology<" in by_cert
    assert "Semiconductor Processing" in column_legend(plates, "certificate") and "Vacuum Technology" in column_legend(plates, "certificate")
    by_college = occupation_block("17-3024", plates)
    assert by_college.count(">Foothill<") == 2 and "Vacuum Technology<" not in by_college
    assert column_legend(plates).count("alg-lg") == 2                          # one college label + the chip key


def _rt_plate():
    rows = [Row("d1", "Diagnose equipment malfunctions.", "t",
                {"RSPT 55B": Cell(2, [Evidence("RSPT 55B", "objectives", 2, "seminar objective", "b")]),
                 "RSPT 50A": Cell(2, [Evidence("RSPT 50A", "objectives", 2, "Demonstrate use of humidity and bland aerosol therapy", "b")]),
                 "RSPT 70A": Cell(1, [Evidence("RSPT 70A", "content", 1, "Aerosol therapy", "b")]),
                 PLO: Cell(2, [Evidence(PLO, "program_outcomes", 2, "entry-level competency", "b")])}),
            Row("d2", "Inspect production equipment.", "t", {"RSPT 70A": Cell(1, [Evidence("RSPT 70A", "lab", 1, "Inspect ventilator circuits", "b")])})]
    return Plate("Foothill College", "foothill", "Associate in Science Degree, Respiratory Therapy", "credit", "121000", "RT", "29-1126", "Respiratory Therapists",
                 [], "", [{"code": "RSPT 55B", "title": "Mediated Studies Ii", "units": 0.5}, {"code": "RSPT 50A", "title": "Respiratory Therapy Procedures", "units": 4.5},
                          {"code": "RSPT 70A", "title": "Clinical Rotation I", "units": 2}], [], rows, short_title="Respiratory Therapy")


def test_dense_cell_shows_the_lead_only_with_cor_tag_and_legend():
    pl = _rt_plate()
    html = occupation_block("29-1126", [pl], columns="certificate")
    assert html.count('class="alg-ev"') == 2                                 # one mark per activity
    assert "RSPT 50A" in html and "RSPT 55B" not in html and "also" not in html   # default lead: same tier, more units; no code list
    assert "Respiratory Therapy Procedures" in html and "Demonstrate use of humidity" in html and 'alg-secx">Course objective<' in html and 'alg-secx">Lab content<' in html and '--t:#2a3450' in html and '--t:#7a869a' in html
    assert "Program outcome" not in html                                     # PLO cells are read, not drawn
    pl.rows[0].lead = {"course": "RSPT 70A", "section": "content", "quote": "Aerosol therapy", "reason": "names the procedure"}
    html = occupation_block("29-1126", [pl], columns="certificate")
    assert "RSPT 70A" in html.split("Inspect production")[0] and 'alg-secx">Course content<' in html        # a stored judgment wins
    pl.rows[0].lead = {"course": "RSPT 99", "section": "content", "quote": "gone", "reason": "stale"}
    assert lead_for(pl.rows[0], pl)["course"] == "RSPT 50A"                                            # a lead no excerpt backs falls to the default
    assert "section of the course outline of record" in column_legend([pl], "certificate")
    assert "section of the course outline of record" not in column_legend([pl])
    sparse = occupation_block("29-1126", [pl])
    assert "Respiratory Therapy Procedures" not in sparse and "Program outcome" not in sparse   # consortium view unchanged


def test_block_intro_and_key():
    from partnerships.alignment_plate import block_key
    pl = _rt_plate()
    html = occupation_block("29-1126", [pl], columns="certificate", intro='<p class="alg-desc"><i>Assesses patients.</i></p>' + block_key())
    assert html.index("SOC 29-1126") < html.index("Assesses patients.") < html.index('alg-key') < html.index("<table")
    assert "swatch" not in block_key() and "<i style" not in block_key() and "CODE" in block_key() and "captions" not in block_key()
    assert 'alg-desc' not in occupation_block("29-1126", [pl], columns="certificate")       # no intro, nothing inserted


def test_rank_leads_judges_multi_excerpt_rows_and_falls_back():
    from partnerships.alignment import rank_leads
    pl = _rt_plate()
    seen = []
    def judge(system, user, schema):
        seen.append(user)
        return {"data": {"choices": [{"activity": 0, "excerpt": 2, "reason": "names aerosol therapy itself"}]}, "error": None}
    rank_leads(pl, complete=judge)
    assert len(seen) == 1 and "[0] activity" in seen[0] and "[1] activity" not in seen[0]     # only the multi-excerpt row is judged
    assert pl.rows[0].lead["course"] == "RSPT 70A" and pl.rows[0].lead["reason"] == "names aerosol therapy itself"
    assert pl.rows[1].lead["course"] == "RSPT 70A" and pl.rows[1].lead["reason"].startswith("default")   # single excerpt: no call
    pl = _rt_plate()
    rank_leads(pl, complete=lambda *a: {"data": None, "error": "boom"})
    assert pl.rows[0].lead["course"] == "RSPT 50A"                                              # failure: tier, units, catalog


def test_pcf_code_spelling():
    assert _pcf_code("ENGR061A") == "ENGR 61A" and _pcf_code("MATH040A") == "MATH 40A" and _pcf_code("DMT084A") == "DMT 84A"
    assert _pcf_code("WRK300MT") == "WRK 300MT" and _pcf_code("MTT020", keep_zeros=True) == "MTT 020"
    assert _pcf_code("ENGR 61A") == "ENGR 61A" and _pcf_code("MATH 040A") == "MATH 40A"
    assert _pcf_code("engr061a") == "ENGR 61A" and _pcf_code("  DMT084A  ") == "DMT 84A"
    assert _pcf_code("061A") == "061A"                       # no department letters: left for the human pass
    assert _pcf_code("COMMC1000") == "COMMC 1000"            # C-ID ids come out wrong on purpose — the _todo names them


def test_scaffold_record_from_coci_and_pcf_rows():
    award = CociAward("FOOTHILL", "094500", "Semiconductor Processing",
                      "Certificate of Achievement requiring 8S/12Q to fewer than 16S/24Q units", "Active", "2023-01-01", "", "43983")
    rows = [{"Course Id": "ENGR061A", "Course Title": "INTRODUCTION TO SEMICONDUCTOR TECHNOLOGY", "Course Status": "Active"},
            {"Course Id": "ENGR101A", "Course Title": "ADVANCED MANUFACTURING", "Course Status": "Active"},
            {"Course Id": "ENGR101A", "Course Title": "ADVANCED MANUFACTURING", "Course Status": "Active"},    # PCF repeats a course per proposal
            {"Course Id": "MATH040A", "Course Title": "QUANTITATIVE REASONING", "Course Status": "Inactive"}]
    rec = scaffold_record(award, rows, college="Foothill College", college_key="foothill", source={"system": "courseleaf"},
                          top_name="Industrial Systems Technology and Maintenance")
    assert [c["code"] for c in rec["courses"]] == ["ENGR 61A", "ENGR 101A"]
    assert rec["certificate"] == "Certificate of Achievement, Semiconductor Processing" and rec["short_title"] == "Semiconductor Processing"
    assert rec["control_number"] == "43983" and rec["top6"] == "094500" and rec["status"] == "Active" and rec["kind"] == "credit"
    assert rec["source"] == {"system": "courseleaf"} and rec["_todo"] and rec["program_outcomes"] == []
    nc = CociAward("FOOTHILL", "094500", "Bridge", "Noncredit program", "Approved", "2023-01-01", "", "00042")
    rec = scaffold_record(nc, [], college="Foothill College", college_key="foothill", source=None)
    assert rec["kind"] == "noncredit" and rec["certificate"] == "Certificate of Completion, Bridge"
    assert rec["source"] == {"system": "TODO"} and rec["courses"] == [] and rec["status"] == "Approved"


def test_occupation_block_lists_chips_and_gaps_and_skips_program_outcomes():
    rows = [Row("d1", "Diagnose equipment malfunctions.", "t",
                {"MTT 020": Cell(2, [Evidence("MTT 020", "outcomes", 2, "q1", "b")]),
                 PLO: Cell(2, [Evidence(PLO, "program_outcomes", 2, "q2", "b")])}),
            Row("d2", "Clean workpieces or finished products.", "t", {}),
            Row("d3", "Inspect production equipment.", "t", {"MTT 012": Cell(1, [Evidence("MTT 012", "lab", 1, "q3", "b")])})]
    mk = lambda college, mid, role: Plate(college, mid, "Cert", "credit", "0935.00", "EMT", "17-3024", "Mechatronics Techs",
                                          ["17-3024"], "", [{"code": "MTT 020", "source_url": "https://x/mtt020"}, {"code": "MTT 012"}], [], rows, role=role)
    html = occupation_block("17-3024", [mk("Mission College", "mission", "paired")], top_n=2)
    assert 'class="chip"' in html and "MTT 020" in html and "chip solid" not in html and "chip ring" not in html
    assert '<a class="chip" href="https://x/mtt020"' in html               # a chip links to its outline
    assert '<b class="chip"' in html                                         # a course without a URL stays a plain chip
    # unevidenced d2 is left out and the next evidenced activity (d3) fills the second slot
    assert "Clean workpieces" not in html and "Inspect production equipment" in html
    assert "no course in the consortium evidences this" not in html
    assert "Program outcomes" not in html and "PLO" not in html           # PLO cells are not chips
    assert "course marks" not in html and "Most from" not in html          # no counts in the report
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


def test_save_readings_round_trips_leads_and_carries_no_connection(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "STORE", tmp_path)
    pl = _plate("Foothill College", "foothill", "17-3024", role="paired", pairing_basis="stated", crosswalk_socs=["17-3026"])
    pl.rows[0].lead = {"course": "C 1", "section": "content", "quote": "q", "reason": "only excerpt"}
    pl.dropped.append({"activity": 1, "course": "C 1", "quote": "x", "why": "adjudicated: a) topic"})
    jp, rp = save_readings("ref-x", {"17-3024": pl}, generated="2026-01-01")
    back = load_readings("ref-x")["17-3024"]
    assert back.rows[0].lead == pl.rows[0].lead and back.courses == pl.courses and back.paired_soc == "17-3024"
    assert back.role == "paired" and "2026-01-01" in jp.read_text() and "### Dropped" in rp.read_text()
    # what the store holds is the reading; a roster's connection is re-applied by view_roster
    monkeypatch.setattr(A, "load_roster", lambda _id: {"id": "r", "programs": [{"program": "ref-x", "paired_soc": "17-3024", "pairing_basis": "roster says"}]})
    monkeypatch.setattr(A, "load_program", lambda ref: {"college": "Foothill College", "college_key": "foothill", "member_id": "foothill"})
    _, plates = view_roster("r")
    assert plates[0].pairing_basis == "roster says" and plates[0].role == "paired"


def test_union_drops_marks_of_a_course_no_longer_on_the_record():
    old = _plate("Mission College", "mission", "17-3024")                       # marks on C 1
    new = Plate("Mission College", "mission", "Cert", "credit", "095600", "Mfg", "17-3024", "Occ", [], "",
                [{"code": "MTT 020"}], [], [Row("d1", "Diagnose equipment malfunctions.", "t", {})])
    merged = _union_plate(new, old)
    assert "C 1" not in merged.rows[0].cells                                    # C 1 left the record; its marks go with it


def test_reread_keeps_a_valid_lead_and_rejudges_only_changed_rows(monkeypatch):
    prev = _plate("Mission College", "mission", "17-3024")
    prev.rows[0].lead = {"course": "C 1", "section": "content", "quote": "q", "reason": "curator"}
    monkeypatch.setattr(A, "load_readings", lambda ref: {"17-3024": prev})
    monkeypatch.setattr(A, "program_outlines", lambda program, refresh=False: {"MTT 020": _outline(), "C 1": _outline()})
    monkeypatch.setattr(A, "get_work_activities", lambda soc: [type("W", (), {"dwa_id": "d1", "dwa": "Diagnose equipment malfunctions.", "task_text": "t"})()])
    monkeypatch.setattr(A, "get_title", lambda soc: "Occ")
    program = {"ref": "r", "college": "Mission College", "member_id": "mission", "college_key": "mission", "certificate": "Cert",
               "courses": [{"code": "MTT 020"}, {"code": "C 1"}], "program_outcomes": [], "source": {}}
    judged = []
    def fake(system, user, schema):
        if "choices" in json.dumps(schema):
            judged.append(user); return {"data": {"choices": [{"activity": 0, "excerpt": 1, "reason": "judge"}]}, "error": None}
        return {"data": {"matches": []}, "error": None}                      # nothing new: excerpts unchanged
    out = read_program(program, ["17-3024"], adjudicate=False, complete=fake)
    assert out["17-3024"].rows[0].lead["reason"] == "curator" and judged == []    # kept, and no judgment asked
    def fake2(system, user, schema):
        if "choices" in json.dumps(schema):
            judged.append(user); return {"data": {"choices": [{"activity": 0, "excerpt": 1, "reason": "judge"}]}, "error": None}
        return {"data": {"matches": [{"activity": 1, "course": "MTT 020", "section": "content", "quote": "Ladder logic programming", "basis": "b"}]}, "error": None}
    out = read_program(program, ["17-3024"], adjudicate=False, complete=fake2)
    assert len(judged) == 1 and out["17-3024"].rows[0].lead["reason"] == "judge"    # a new excerpt on the row → re-judged


def test_partial_reread_requires_accumulation():
    import pytest
    with pytest.raises(ValueError):
        read_program({"ref": "r"}, ["17-3024"], units="plo", accumulate=False)


def test_rank_leads_maps_choices_by_row_index_and_ignores_strays():
    from partnerships.alignment import rank_leads
    rows = [Row("d0", "Single.", "t", {"C 1": Cell(1, [Evidence("C 1", "content", 1, "only", "b")])}),
            Row("d1", "Multi A.", "t", {"C 1": Cell(1, [Evidence("C 1", "content", 1, "a0", "b")]), "C 2": Cell(1, [Evidence("C 2", "content", 1, "a1", "b")])}),
            Row("d2", "Multi B.", "t", {"C 1": Cell(1, [Evidence("C 1", "content", 1, "b0", "b")]), "C 2": Cell(1, [Evidence("C 2", "content", 1, "b1", "b")])})]
    pl = Plate("Foothill College", "foothill", "Cert", "credit", "095600", "Mfg", "17-3024", "Occ", [], "",
               [{"code": "C 1", "units": 1}, {"code": "C 2", "units": 1}], [], rows)
    seen = []
    def judge(system, user, schema):
        seen.append(user)
        return {"data": {"choices": [{"activity": 1, "excerpt": 1, "reason": "A→a1"}, {"activity": 2, "excerpt": 0, "reason": "B→b0"},
                                     {"activity": 9, "excerpt": 0, "reason": "stray"}]}, "error": None}
    rank_leads(pl, complete=judge)
    assert "[1] activity" in seen[0] and "[2] activity" in seen[0] and "[0] activity" not in seen[0]
    assert pl.rows[1].lead["quote"] == "a1" and pl.rows[2].lead["quote"] == "b0" and pl.rows[0].lead["quote"] == "only"
