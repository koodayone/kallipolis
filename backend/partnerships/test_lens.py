"""Integration tests for the L1 lens substrate (lens.build_lens).

Graph-backed: these assert the *contract* both renderers depend on — occupation
atom, openings ranking, the partner graph, per-occupation employers, provenance,
and the deliberate ABSENCE of any opinionated score or cross-occupation supply
sum. Skipped automatically where Neo4j is unreachable.

Runnable two ways: `pytest partnerships/test_lens.py`, or `python -m
partnerships.test_lens` (runs every test_* and reports) — the latter so it can be
verified inside the backend container, which has the graph but not pytest.
"""

from __future__ import annotations

from partnerships.lens import FIELD_AUTHORITY, SOURCES, LensOccupation, Play, build_lens

# A member×sector known to resolve with supply (Foothill runs an adm program).
_MEMBER, _SECTOR = "foothill", "adm"
# The SVAMP "Manufacturing Technician" play — O*NET's top-3 SOC matches.
_PLAY = Play(id="manufacturing-technician", title="Manufacturing Technician",
             sector="adm", socs=("17-3026", "51-9141", "17-3024"))


def _graph_ok() -> bool:
    try:
        build_lens(_MEMBER, sector=_SECTOR)
        return True
    except Exception as e:  # connection / env — not an assertion failure
        if e.__class__.__name__ in ("ValueError", "LookupError"):
            raise
        return False


def test_sector_lens_is_openings_ranked_occupation_grain():
    L = build_lens(_MEMBER, sector=_SECTOR)
    assert L.occupations, "expected occupations for a member with supply"
    openings = [o.annual_openings for o in L.occupations]
    assert openings == sorted(openings, reverse=True), "occupations must rank by openings desc"
    assert all(isinstance(o, LensOccupation) for o in L.occupations)
    assert L.scope.member.kind == "college"
    assert len(L.scope.partner_universe) > 1, "a college lens expands to its consortium peers"


def test_partner_graph_and_membership_are_facts_not_scores():
    L = build_lens(_MEMBER, sector=_SECTOR)
    # Every occupation carries its feeders (the partner graph); each feeder's
    # is_member is a plain fact about consortium membership.
    assert all(o.feeders for o in L.occupations)
    member_names = {f.college for o in L.occupations for f in o.feeders if f.is_member}
    assert member_names == {L.scope.member.name}, "is_member must mean exactly the scope member"
    assert any(o.member_feeds for o in L.occupations)


def test_no_opinionated_score_and_no_cross_occupation_supply_sum():
    L = build_lens(_MEMBER, sector=_SECTOR)
    o = L.occupations[0]
    # The rejected opinion layer must not exist on the atom.
    for banned in ("priority_score", "role", "anchor", "gap", "supply", "coverage"):
        assert not hasattr(o, banned), f"lens occupation must not carry '{banned}'"


def test_employers_are_per_occupation_and_relevance_ranked():
    L = build_lens(_MEMBER, sector=_SECTOR)
    withemp = [o for o in L.occupations if o.employers]
    assert withemp, "at least one occupation should surface employers"
    for o in withemp:
        rel = [e.relevance for e in o.employers]
        assert rel == sorted(rel, reverse=True), "employers rank by relevance desc"


def test_play_is_exactly_the_curated_set():
    R = build_lens("svamp", play=_PLAY)
    assert R.scope.slice.kind == "play"
    assert R.scope.slice.title == "Manufacturing Technician"
    assert {o.soc for o in R.occupations} == set(_PLAY.socs)
    openings = [o.annual_openings for o in R.occupations]
    assert openings == sorted(openings, reverse=True)


def test_provenance_is_complete_and_resolvable():
    L = build_lens(_MEMBER, sector=_SECTOR)
    assert {s.id for s in L.sources} == set(SOURCES)
    assert all(src in SOURCES for src in FIELD_AUTHORITY.values()), "every field maps to a known authority"
    # competencies are a report-layer concern (curated from the O*NET bundle at
    # report time), deliberately NOT an L1 field.
    assert not hasattr(L.occupations[0], "competencies")


if __name__ == "__main__":
    import traceback

    if not _graph_ok():
        print("SKIP: graph unreachable")
        raise SystemExit(0)
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
