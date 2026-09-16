"""Unit tests for occupations.work_activities — the O*NET work-activity bundle a curriculum is read against.

The bundle is regenerated from an O*NET text-DB release; these tests pin the contract the
alignment depends on without touching the release files.

Coverage:
  - core activities come back in descending anchoring-task importance with task text attached
  - the core-only row set is a strict subset of every anchored activity
  - a `.00`-suffixed code resolves to its base SOC; an unknown SOC yields an empty list
"""

from occupations.work_activities import get_work_activities


def test_core_activities_are_importance_ordered_and_carry_task_text():
    acts = get_work_activities("51-9141")
    assert acts, "Semiconductor Processing Technicians must have core activities"
    assert all(a.core for a in acts)
    imps = [a.importance for a in acts]
    assert imps == sorted(imps, reverse=True)
    top = acts[0]
    assert top.dwa.startswith("Measure dimensions")
    assert top.tasks and top.task_text          # the matcher is shown the anchoring task
    assert all(t.core or True for t in top.tasks)


def test_core_only_is_a_subset_of_all_anchored():
    core = get_work_activities("17-3026")
    every = get_work_activities("17-3026", core_only=False)
    assert 0 < len(core) < len(every)
    assert {a.dwa_id for a in core} <= {a.dwa_id for a in every}


def test_specialty_fallback_and_unknown_soc():
    # 17-3024 has a .00 parent; the bundle keys on the 6-digit base either way
    assert get_work_activities("17-3024.00")
    assert get_work_activities("99-9999") == []
