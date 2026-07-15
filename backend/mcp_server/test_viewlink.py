"""Coherence + deep-link tests for viewlink.py.

Every analytical form must have a CONSIDERED dashboard-view decision — either it maps to a lens
(``_FORM_LENS``) or it is DELIBERATELY unavailable (``INTENTIONALLY_UNMAPPED``). This is the sibling
of the TOOL_NAME coherence test in test_mcp_server.py: it guards the exact break that shipped
``compare`` with no corroborating "verify with your own eyes" link, invisible until an eval caught it.

Pure string-building — no graph — so it gates on every PR.
"""
from __future__ import annotations

import mcp_server.catalog as C
from mcp_server import viewlink as V

_COORD = dict(instance_id="smccd-adm", member_id="smccd", sector_id="adm")


def test_every_catalog_form_has_a_view_decision():
    """Each catalog form emits a corroborating view OR is declared ``INTENTIONALLY_UNMAPPED`` — no
    silent fall-through to 'unavailable'. A new form that forgets a view decision fails here."""
    for form_id in C.FORMS:
        if form_id in V.INTENTIONALLY_UNMAPPED:
            assert V.view_link(form_id, **_COORD).status == "unavailable", form_id
        elif form_id == "pathway":                    # unit-discriminated: both legs must resolve
            assert V.view_link("pathway", top6="095630", **_COORD).status == "ok"
            assert V.view_link("pathway", soc="51-4041", **_COORD).status == "ok"
        elif form_id == "compare":                    # unit-discriminated: all three legs must resolve
            for ut in ("program", "occupation", "college"):
                assert V.view_link("compare", unit_type=ut, **_COORD).status == "ok", ut
        else:
            assert V.view_link(form_id, **_COORD).status == "ok", form_id


def test_intentionally_unmapped_is_disjoint_from_mapped():
    """A form is EITHER mapped OR intentionally unavailable, never both — the partition is clean."""
    assert V.INTENTIONALLY_UNMAPPED.isdisjoint(V._FORM_LENS)


def test_compare_lens_follows_unit_type():
    """The regression under fix: compare carries a real deep-link, and its lens tracks unit_type
    (program → programs, occupation → occupations, college → the coverage panel)."""
    prog = V.view_link("compare", unit_type="program", **_COORD)
    occ = V.view_link("compare", unit_type="occupation", **_COORD)
    coll = V.view_link("compare", unit_type="college", **_COORD)
    assert prog.status == "ok" and "lens=programs" in prog.url
    assert occ.status == "ok" and "lens=occupations" in occ.url
    assert coll.status == "ok" and "panel=programs.coverage" in coll.url
    assert V.view_link("compare", **_COORD).status == "ok"        # defaults to program, never broken


def test_compare_unknown_unit_type_is_unavailable_not_broken():
    """A bogus unit_type falls through to an honest 'unavailable', never a malformed URL."""
    assert V.view_link("compare", unit_type="bogus", **_COORD).status == "unavailable"
