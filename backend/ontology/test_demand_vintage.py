"""Unit tests for ontology/demand_vintage.py — one vintage across every copy of the COE demand data.

The file-level checks run here so a refresh that updates the export but not a derived copy
(the generated universe, the sector join, the eval seed, the characterization corpus, an
authored figure in a report definition, the skill's worked example) fails CI rather than
shipping two editions at once. The graph check needs Neo4j and runs from the CLI.

Coverage:
  - every file-level check agrees with the bundled export
  - a value that drifts is reported: an occupations.json row with a different openings figure fails the values check
  - an authored figure that matches neither an occupation's openings nor their sum is reported stale
  - the regional totals line reports the nine regions' sum against the statewide row without failing
"""
import json

from ontology import demand_vintage as DV


def test_every_copy_agrees_with_the_bundled_export():
    findings = DV.run_checks(graph=False)
    bad = [f for f in findings if not f.ok]
    assert not bad, "\n".join(f"{f.check}: {f.detail}" for f in bad)


def test_a_drifted_value_is_reported(tmp_path, monkeypatch):
    x = DV.load_export()
    occs = json.loads(DV.OCCUPATIONS.read_text())
    occs[0]["regions"]["Bay"]["annual_openings"] = (occs[0]["regions"]["Bay"]["annual_openings"] or 0) + 10
    p = tmp_path / "occupations.json"; p.write_text(json.dumps(occs))
    monkeypatch.setattr(DV, "OCCUPATIONS", p)
    values = next(f for f in DV.check_occupations_json(x) if f.check == "occupations.json values")
    assert not values.ok and values.detail.startswith("1 ")


def test_a_stale_authored_figure_is_reported(tmp_path, monkeypatch):
    x = DV.load_export()
    d = {"member": "foothill", "socs": ["29-1126"], "demand_note": "…has roughly 999 openings a year in the Bay Area."}
    (tmp_path / "zz-test.json").write_text(json.dumps(d))
    monkeypatch.setattr(DV, "SAVED", tmp_path)
    f = DV.check_authored_figures(x)[0]
    assert not f.ok and "999" in f.detail


def test_regional_totals_are_reported_against_the_statewide_row():
    x = DV.load_export()
    f, = DV.check_regional_totals(x)
    assert f.ok and "9 regions sum to" in f.detail and "vs CA" in f.detail and "SCC" in f.detail
