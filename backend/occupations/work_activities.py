"""O*NET work activities — the layer a curriculum is READ AGAINST.

An occupation's *detailed work activities* (DWAs) are O*NET's shared vocabulary of what
the work consists of: roughly two thousand statements, each written as one verb and one
object ("Diagnose equipment malfunctions"), shared across all occupations so that two
programs matched against two occupations are matched against the same kind of sentence.
That altitude is also the one course learning outcomes are written at, which is why the
DWA — not the task, not the knowledge domain — is the unit the alignment counts.

Tasks are where the DWA gets its meaning and its rank. Every DWA an occupation carries
is anchored to one or more of that occupation's tasks, and tasks are the only O*NET
layer written for a single occupation by its own incumbents and rated by them. So:

  * the ROW SET for an occupation is the DWAs anchored to its Core tasks — O*NET's own
    binary (a Core task is one most incumbents perform and rate as important), not a
    threshold we invent;
  * the ROW ORDER is the highest incumbent importance among the anchoring tasks, so the
    plate reads "matters most" at the top without printing a number;
  * the TASK TEXT travels with the DWA, because a matcher shown only the DWA title will
    both miss matches (the DWA for "adhere to health, safety and environmental
    regulations" is titled "Monitor activities affecting environmental quality") and
    over-credit generic ones ("Clean workpieces or finished products" means wafer
    cleaning in chemical baths under Semiconductor Processing).

Like `occupations.competencies`, this is a report-layer bundle read at report time, not
graph state. Two files under `ontology/data/`, both regenerated from an O*NET text-DB
release directory by `build_bundle`:

  onet_work_activities.tsv   one row per (SOC, DWA): rank, ids, titles, core flag,
                             importance, and the anchoring task ids
  onet_tasks.tsv.gz          one row per (SOC, task): the statement, Core/Supplemental,
                             importance — joined at read time

Release: O*NET 31.0 (August 2026). The 31.0 text DB renamed the DWA files' columns to
`DWA Element ID` / `DWA Element Name` and moved the IWA/GWA hierarchy into
`GWAs to IWAs to DWAs.txt`; the builder reads those names.
"""

from __future__ import annotations

import csv
import gzip
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA = Path(__file__).parent.parent / "ontology" / "data"
ACTIVITIES_PATH = _DATA / "onet_work_activities.tsv"
TASKS_PATH = _DATA / "onet_tasks.tsv.gz"

#: Stated like the other bundles' vintages so a surface can cite currency.
ONET_VINTAGE = "O*NET 31.0 database (August 2026), U.S. Department of Labor"


@dataclass(frozen=True)
class Task:
    task_id: str
    text: str
    core: bool
    importance: float | None   # incumbent importance on O*NET's 1–5 scale; None if unrated


@dataclass(frozen=True)
class WorkActivity:
    soc: str                    # 6-digit base SOC, e.g. "51-9141"
    rank: int                   # 1 = highest anchoring-task importance
    dwa_id: str
    dwa: str                    # the DWA statement
    iwa: str                    # its intermediate work activity (the roll-up above it)
    core: bool                  # anchored to at least one Core task
    importance: float           # max importance among anchoring tasks (0 if all unrated)
    tasks: tuple[Task, ...]     # the anchoring tasks, importance-descending

    @property
    def task_text(self) -> str:
        """The anchoring tasks as one line — what the matcher is shown beside the DWA."""
        return " · ".join(t.text for t in self.tasks)


_activities: dict[str, list[WorkActivity]] | None = None


def _load() -> dict[str, list[WorkActivity]]:
    global _activities
    if _activities is not None:
        return _activities
    tasks: dict[tuple[str, str], Task] = {}
    with gzip.open(TASKS_PATH, "rt", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            im = float(r["importance"]) if r["importance"] else None
            tasks[(r["soc_code"], r["task_id"])] = Task(r["task_id"], r["task"], r["core"] == "Y", im)
    out: dict[str, list[WorkActivity]] = defaultdict(list)
    with open(ACTIVITIES_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            soc = r["soc_code"]
            anchors = tuple(sorted((tasks[(soc, t)] for t in r["task_ids"].split("|") if (soc, t) in tasks),
                                   key=lambda t: -(t.importance or 0)))
            out[soc].append(WorkActivity(soc, int(r["rank"]), r["dwa_id"], r["dwa"], r["iwa"],
                                         r["core"] == "Y", float(r["importance"]), anchors))
    for soc in out:
        out[soc].sort(key=lambda a: a.rank)
    _activities = dict(out)
    logger.info("Loaded O*NET work activities for %d SOCs", len(_activities))
    return _activities


def get_work_activities(soc: str, *, core_only: bool = True) -> list[WorkActivity]:
    """The occupation's DWAs in importance order. `core_only` (the editorial default)
    keeps the ones anchored to a Core task; False returns every anchored DWA."""
    rows = _load().get(soc[:7], [])
    return [a for a in rows if a.core] if core_only else list(rows)


# ── Bundle maintenance ─────────────────────────────────────────────────────────
def build_bundle(onet_dir: str) -> None:
    """Regenerate both bundle files from an O*NET text-DB release directory
    (e.g. `db_31_0_text`). Prefers the `.00` parent occupation; a base SOC with no
    parent row falls back to its first specialty, as the competency bundle does."""
    d = Path(onet_dir)

    def rd(name: str):
        with open(d / name, encoding="utf-8", newline="") as f:
            yield from csv.DictReader(f, delimiter="\t")

    tasks: dict[tuple[str, str], dict] = {}
    for r in rd("Task Statements.txt"):
        tasks[(r["O*NET-SOC Code"], r["Task ID"])] = {"text": r["Task"], "type": r["Task Type"], "im": None}
    for r in rd("Task Ratings.txt"):
        k = (r["O*NET-SOC Code"], r["Task ID"])
        if k in tasks and r["Scale ID"] == "IM" and r.get("Recommend Suppress") != "Y":
            tasks[k]["im"] = float(r["Data Value"])

    dwa_ref = {r["DWA Element ID"]: r for r in rd("GWAs to IWAs to DWAs.txt")}
    iwa_ref = {r["IWA Element ID"]: r["IWA Element Name"] for r in rd("GWAs to IWAs.txt")}

    anchors: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))  # onet_soc -> dwa -> [task_id]
    for r in rd("Tasks to DWAs.txt"):
        k = (r["O*NET-SOC Code"], r["Task ID"])
        if k in tasks:
            anchors[k[0]][r["DWA Element ID"]].append(k[1])

    # choose one O*NET-SOC per base SOC: the .00 parent, else the first specialty
    chosen: dict[str, str] = {}
    for code in sorted(anchors):
        base, suffix = code[:7], code[8:]
        if suffix == "00" or base not in chosen:
            chosen[base] = code if suffix == "00" else chosen.get(base, code)

    act_rows: list[tuple] = []
    task_rows: list[tuple] = []
    for base, code in sorted(chosen.items()):
        rows = []
        for dwa_id, tids in anchors[code].items():
            ts = [tasks[(code, t)] for t in tids]
            im = max((t["im"] or 0.0) for t in ts)
            core = any(t["type"] == "Core" for t in ts)
            ref = dwa_ref.get(dwa_id)
            if ref is None:
                continue
            rows.append((im, core, dwa_id, ref["DWA Element Name"], iwa_ref.get(ref["IWA Element ID"], ""), tids))
        rows.sort(key=lambda x: (-x[0], x[3]))
        for rank, (im, core, dwa_id, dwa, iwa, tids) in enumerate(rows, 1):
            act_rows.append((base, rank, dwa_id, dwa, iwa, "Y" if core else "N", f"{im:.2f}", "|".join(tids)))
        for (c, tid), t in tasks.items():
            if c == code:
                task_rows.append((base, tid, t["text"], "Y" if t["type"] == "Core" else "N",
                                  "" if t["im"] is None else f"{t['im']:.2f}"))

    with open(ACTIVITIES_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["soc_code", "rank", "dwa_id", "dwa", "iwa", "core", "importance", "task_ids"])
        w.writerows(act_rows)
    with gzip.open(TASKS_PATH, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["soc_code", "task_id", "task", "core", "importance"])
        w.writerows(task_rows)
    print(f"wrote {ACTIVITIES_PATH} ({len(act_rows)} rows) and {TASKS_PATH} ({len(task_rows)} rows) "
          f"for {len(chosen)} SOCs")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        build_bundle(sys.argv[1])
    else:
        for soc in ("51-9141", "17-3026", "17-3024", "51-4041"):
            acts = get_work_activities(soc)
            print(f"\n{soc}: {len(acts)} core work activities")
            for a in acts:
                print(f"  {a.importance:.2f}  {a.dwa}")
