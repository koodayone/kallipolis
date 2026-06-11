"""Export DataMart per-college summary reports as wide CSVs (one time period per
column), for the 26 Bay Area colleges, back to a floor period (default Fall 2021
/ academic year 2021-2022).

Three report profiles, all on the same DevExpress ASPx site:

  credit  -> Courses/Credit_Course_Summary.aspx
             rows: Six Digits TOP; columns: term; value: Enrollment Count
  ncredit -> Courses/NCredit_Course_Summary.aspx   (same controls as credit)
             rows: Six Digits TOP; columns: term; value: Enrollment Count
  awards  -> Outcomes/Program_Awards.aspx
             rows: Award Type -> Six Digits TOP; columns: academic year;
             value: Chancellor's-Office-Approved award count; TOP filter = all

Key lessons (the reason this works at all):
  * The report only *builds* on a GENUINE button click. The DevExpress buttons
    carry capture-phase click handlers inside an ASP.NET AJAX UpdatePanel; a
    scripted form submit (requestSubmit/__doPostBack) posts but returns an empty
    report. Every button below is a real Playwright click.
  * Dropdown items must be selected by clicking the list item (which syncs the
    editor value the server reads); the client SelectIndices API sets only a
    hidden field and the server ignores it.
  * Awards adds two parameter widgets the course reports lack: an Award Type
    combo and a "(All Programs)" TOP tree filter that defaults to *empty* (no
    selection -> no data), so it must be checked before running.
  * DataMart drops any time column with zero data, so each college's raw export
    is reindexed onto a fixed canonical column set; real gaps (e.g. Foothill has
    no Fall 2023; semester colleges have no Winter terms) show as blanks.

Output: backend/ontology/datamart/<profile_dir>/<backend_key>.csv
Resumable: a college whose CSV already exists (non-empty) is skipped.

Usage:
    python -m pipeline.datamart_export credit
    python -m pipeline.datamart_export ncredit
    python -m pipeline.datamart_export awards
    python -m pipeline.datamart_export ncredit --only laney
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pipeline.datamart_keys import csv_name_to_backend_key

# Authoritative Bay Area set, mirrored from pipeline/reload.py BAY_AREA.
# (Inlined to avoid importing reload.py, which pulls in neo4j.)
BAY_AREA = [
    "foothill", "deanza", "ccsf", "laney", "merritt", "berkeleycc",
    "alameda", "skyline", "canada", "csm", "losmedanos", "diablo",
    "contracosta", "evergreen", "sanjosecity", "marin", "santarosa",
    "napavalley", "solano", "westvalley", "mission", "ohlone",
    "chabot", "laspositas", "cabrillo", "gavilan",
]

_DATAMART = Path(__file__).parent.parent / "ontology" / "datamart"
_CATALOG = Path(__file__).parent / "catalog_sources.json"


def catalog_keys() -> list[str]:
    """Every college key in catalog_sources.json (the full ontology set)."""
    import json
    return list(json.loads(_CATALOG.read_text())["colleges"].keys())

# ---- Shared DevExpress control ids (identical across all three reports) ----
SDC_BTN = "#ASPxRoundPanel1_ASPxComboBoxSDC_B-1"
SDC_COLLEGEWIDE = "#ASPxRoundPanel1_ASPxComboBoxSDC_DDD_L_LBI2T0"
COLL_BTN = "#ASPxRoundPanel1_ASPxDropDownEditDistColl_B-1"
COLL_LIST = "ASPxRoundPanel1_ASPxDropDownEditDistColl_DDD_DDTC_checkListBoxDistColl"
COLL_CLOSE = "#ASPxRoundPanel1_ASPxDropDownEditDistColl_DDD_DDTC_ASPxButtonDistColl"
# The time selector is named "Term" in markup even on the awards report (where
# it holds academic years).
TIME_BTN = "#ASPxRoundPanel1_ASPxDropDownEditTerm_B-1"
TIME_LIST = "ASPxRoundPanel1_ASPxDropDownEditTerm_DDD_DDTC_checkListBoxTerm"
TIME_EDIT = "#ASPxRoundPanel1_ASPxDropDownEditTerm_I"
TIME_CLOSE = "#ASPxRoundPanel1_ASPxDropDownEditTerm_DDD_DDTC_ASPxButtonTerm"
RUN_REPORT = "#ASPxRoundPanel1_RunReportASPxButton"
UPDATE_REPORT = "#ASPxRoundPanel3_UpdateReport"
EXPORT_CSV_RADIO = "#listExportFormat_0"
EXPORT_BTN = "#buttonSaveAs"

# Course reports (credit/ncredit): Six Digits TOP is RowOptions[4]; the three
# metric columns are ColumnOptions[0..2] = Sections Count / FTES / Enrollment.
COURSE_ROW_TOP = "#ASPxRoundPanel3_RowOptions_4"
COURSE_COL_SECTIONS = "#ASPxRoundPanel3_ColumnOptions_0"
COURSE_COL_FTES = "#ASPxRoundPanel3_ColumnOptions_1"
# Credit only: RowOptions[0] = Credit Status. Adding it nests rows as
# College -> Credit Status -> TOP6, preserving the Degree-Applicable /
# Not-Degree-Applicable / (noncredit handled separately) decomposition that
# the /svamp view consumes. (On the noncredit report RowOptions[0] is
# "Accounting Method", not a family — so this is credit-only.)
CREDIT_ROW_STATUS = "#ASPxRoundPanel3_RowOptions_0"

# Awards report extra widgets + breakdown checkboxes.
AWTYPE_BTN = "#ASPxRoundPanel1_ASPxComboBoxAWType_B-1"
AWTYPE_EDIT = "#ASPxRoundPanel1_ASPxComboBoxAWType_I"
AWTYPE_LIST = "ASPxRoundPanel1_ASPxComboBoxAWType_DDD_L"
TOP_TREE_BTN = "#ASPxRoundPanel1_ASPxDropDownEditTOP_B-1"
TOP_TREE_ROOT = ("#ASPxRoundPanel1_ASPxDropDownEditTOP_DDD_DDTC_"
                 "ASPxCallbackPanel1_ASPxTreeView1_N0_D")
TOP_TREE_CLOSE = "#ASPxRoundPanel1_ASPxDropDownEditTOP_DDD_DDTC_ASPxButtonTerm"
AW_OPT_AWARDTYPE = "#ASPxRoundPanel3_TopOptions_0"
AW_OPT_SIXDIGIT = "#ASPxRoundPanel3_TopOptions_4"

SEASON = {"Winter": 0, "Spring": 1, "Summer": 2, "Fall": 3}


def log(msg: str) -> None:
    print(msg, flush=True)


def term_key(label: str):
    """Sortable (year, season) key for 'Fall 2021'."""
    p = label.strip().split()
    if len(p) == 2 and p[0] in SEASON and p[1].isdigit():
        return (int(p[1]), SEASON[p[0]])
    return None


def year_key(label: str):
    """Sortable (end_year,) key for 'Annual 2021-2022'."""
    m = re.search(r"(\d{4})-(\d{4})", label or "")
    return (int(m.group(2)),) if m else None


# ---- Report profiles ----
PROFILES = {
    "credit": {
        "url": "https://datamart.cccco.edu/Courses/Credit_Course_Summary.aspx",
        "dir": "credit_course_summary",
        "kind": "course",
        "time_key": term_key,
        "floor": "Fall 2021",
        "subfamily_row": CREDIT_ROW_STATUS,   # College -> Credit Status -> TOP6
    },
    "ncredit": {
        "url": "https://datamart.cccco.edu/Courses/NCredit_Course_Summary.aspx",
        "dir": "ncredit_course_summary",
        "kind": "course",
        "time_key": term_key,
        "floor": "Fall 2021",
    },
    "awards": {
        "url": "https://datamart.cccco.edu/Outcomes/Program_Awards.aspx",
        "dir": "program_awards",
        "kind": "awards",
        "time_key": year_key,
        "floor": "Annual 2021-2022",
        "award_type": "Chancellor's Office Approved Awards",
    },
}


def wait_dx(pg, settle_ms: int = 1200) -> None:
    try:
        pg.wait_for_load_state("networkidle", timeout=45000)
    except Exception:
        pass
    for _ in range(120):
        try:
            busy = pg.evaluate(
                "()=>[...document.querySelectorAll(\"[id$='_LP'],[id*='LoadingPanel']\")]"
                ".some(e=>e.offsetParent!==null)"
            )
        except Exception:
            busy = False
        if not busy:
            break
        pg.wait_for_timeout(200)
    pg.wait_for_timeout(settle_ms)


def list_items(pg, list_id: str):
    obj = list_id.split("_")[-1]
    return pg.evaluate(
        f"()=>{{const c={obj},n=c.GetItemCount(),o=[];"
        f"for(let i=0;i<n;i++)o.push([i,c.GetItem(i).text]);return o;}}"
    )


def pick_collegewide(pg) -> None:
    pg.click(SDC_BTN)
    pg.wait_for_timeout(400)
    pg.click(SDC_COLLEGEWIDE)
    wait_dx(pg)


def select_college(pg, key: str) -> str:
    pg.click(COLL_BTN)
    pg.wait_for_timeout(700)
    items = list_items(pg, COLL_LIST)
    idx = next(
        (i for i, t in items
         if t and t.strip() != "(Select All)"
         and csv_name_to_backend_key(t.strip()) == key),
        None,
    )
    if idx is None:
        raise RuntimeError(f"college key {key!r} not found in DataMart list")
    name = next(t.strip() for i, t in items if i == idx)
    pg.click(f"#{COLL_LIST}_LBI{idx}T1")
    pg.wait_for_timeout(400)
    pg.click(COLL_CLOSE)
    pg.wait_for_timeout(500)
    return name


def _time_selected_indices(pg) -> set:
    obj = TIME_LIST.split("_")[-1]
    return set(pg.evaluate(f"()=>{obj}.GetSelectedIndices()") or [])


def select_time(pg, profile) -> list[str]:
    """Check every time period >= the floor; verify + retry dropped clicks."""
    keyfn, floor = profile["time_key"], profile["time_key"](profile["floor"])
    pg.click(TIME_BTN)
    pg.wait_for_timeout(700)
    items = list_items(pg, TIME_LIST)
    want = {i: t.strip() for i, t in items
            if t and keyfn(t.strip()) and keyfn(t.strip()) >= floor}
    for _ in range(6):
        missing = [i for i in want if i not in _time_selected_indices(pg)]
        if not missing:
            break
        for i in missing:
            pg.click(f"#{TIME_LIST}_LBI{i}T1")
            pg.wait_for_timeout(250)
    else:
        still = [want[i] for i in want if i not in _time_selected_indices(pg)]
        raise RuntimeError(f"could not select time periods: {still}")
    pg.click(TIME_CLOSE)
    pg.wait_for_timeout(500)
    return [want[i] for i in sorted(want)]


def set_award_type(pg, label: str) -> None:
    pg.click(AWTYPE_BTN)
    pg.wait_for_timeout(500)
    opts = pg.evaluate(
        f"()=>[...document.querySelectorAll(\"[id*='{AWTYPE_LIST}'] [id*='_LBI']\")]"
        ".map(e=>[e.id,(e.textContent||'').trim()])"
    )
    target = next((eid for eid, txt in opts if txt == label and eid.endswith("T0")), None)
    if not target:
        raise RuntimeError(f"award type {label!r} not in combo")
    pg.click(f"#{target}")
    wait_dx(pg, 1200)


def select_all_top(pg) -> None:
    """Check the '(All Programs)' root of the TOP tree filter (else no data)."""
    pg.click(TOP_TREE_BTN)
    pg.wait_for_timeout(1000)
    pg.click(TOP_TREE_ROOT)
    wait_dx(pg, 1500)
    pg.click(TOP_TREE_CLOSE)
    pg.wait_for_timeout(500)


def configure_and_run(pg, profile) -> None:
    pg.click(RUN_REPORT)
    wait_dx(pg, 2500)
    if profile["kind"] == "course":
        pg.click(COURSE_ROW_TOP)                       # rows by Six Digits TOP
        sub = profile.get("subfamily_row")             # credit: + Credit Status
        if sub and not pg.is_checked(sub):
            pg.click(sub)
        if pg.is_checked(COURSE_COL_SECTIONS):
            pg.click(COURSE_COL_SECTIONS)              # drop Sections Count
        if pg.is_checked(COURSE_COL_FTES):
            pg.click(COURSE_COL_FTES)                  # drop Sections FTES
    else:  # awards: rows by Award Type -> Six Digits TOP
        if not pg.is_checked(AW_OPT_AWARDTYPE):
            pg.click(AW_OPT_AWARDTYPE)
        if not pg.is_checked(AW_OPT_SIXDIGIT):
            pg.click(AW_OPT_SIXDIGIT)
    pg.click(UPDATE_REPORT)
    wait_dx(pg, 3000)


def export_csv(pg, out_path: Path) -> int:
    pg.check(EXPORT_CSV_RADIO)
    with pg.expect_download(timeout=40000) as di:
        pg.click(EXPORT_BTN)
    di.value.save_as(str(out_path))
    return out_path.stat().st_size


def read_canonical_times(pg, profile) -> list[str]:
    """All time labels >= floor present in the dropdown, oldest -> newest."""
    pg.goto(profile["url"], timeout=60000, wait_until="domcontentloaded")
    wait_dx(pg)
    pg.click(TIME_BTN)
    pg.wait_for_timeout(700)
    keyfn, floor = profile["time_key"], profile["time_key"](profile["floor"])
    labels = [t.strip() for _, t in list_items(pg, TIME_LIST)
              if t and keyfn(t.strip()) and keyfn(t.strip()) >= floor]
    return sorted(labels, key=keyfn)


def normalize_export(raw_path: Path, canonical: list[str], out_path: Path) -> None:
    """Reindex a raw DataMart CSV onto the canonical time columns, blank-filling
    periods DataMart dropped. Leading label columns (2 for courses, 3 for
    awards) are detected from the header and preserved."""
    rows = list(csv.reader(raw_path.read_text(encoding="utf-8", errors="replace").splitlines()))
    header = rows[0] if rows else []
    lead = next((j for j, c in enumerate(header) if c.strip()), len(header))
    time_at = {c.strip(): j for j, c in enumerate(header[lead:], start=lead) if c.strip()}
    out = [[""] * lead + canonical]
    for r in rows[1:]:
        if not r:
            continue
        labels = [r[j] if j < len(r) else "" for j in range(lead)]
        vals = [r[time_at[t]] if t in time_at and time_at[t] < len(r) else "" for t in canonical]
        out.append(labels + vals)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out)


def export_college(pg, profile, key: str, canonical: list[str], out_path: Path) -> None:
    pg.goto(profile["url"], timeout=60000, wait_until="domcontentloaded")
    wait_dx(pg)
    pick_collegewide(pg)
    name = select_college(pg, key)
    if profile["kind"] == "awards":
        set_award_type(pg, profile["award_type"])
        select_all_top(pg)
    select_time(pg, profile)
    configure_and_run(pg, profile)
    raw = out_path.with_suffix(".raw.csv")
    size = export_csv(pg, raw)
    # A real report carries a "<College> Total" row; an empty/failed build shows
    # only "Grand Total". Size is not a valid signal — some colleges genuinely
    # have just one or two noncredit programs (Solano: one), so a 86-byte file
    # can be correct.
    text = raw.read_text(errors="replace")
    if f"{name} Total" not in text:
        raw.unlink(missing_ok=True)
        # The report BUILT (shows "Grand Total") but this college has no records
        # in scope — e.g. colleges whose noncredit runs through a separate
        # continuing-ed entity (Fullerton, American River) have zero noncredit.
        # That's a real zero, not a failure: write an explicit empty placeholder
        # so the set stays complete and the zero is visible.
        if "Grand Total" in text:
            lead = 3 if profile["kind"] == "awards" else 2
            with out_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([""] * lead + canonical)
                w.writerow([f"{name} Total"] + [""] * (lead - 1 + len(canonical)))
            log(f"    {name}: 0 records (empty placeholder)")
            return
        raise RuntimeError(f"empty/failed report for {key} ({size} bytes)")
    normalize_export(raw, canonical, out_path)
    raw.unlink(missing_ok=True)
    gaps = [t for t in canonical if t not in text]
    note = f", gaps: {gaps}" if gaps else ""
    log(f"    {name}: {len(canonical)-len(gaps)}/{len(canonical)} periods with data{note}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", choices=list(PROFILES))
    ap.add_argument("--only", help="single backend college key")
    ap.add_argument("--all", action="store_true",
                    help="every catalog college (default: the 26 Bay Area)")
    ap.add_argument("--force", action="store_true",
                    help="re-export even if the CSV already exists")
    ap.add_argument("--floor", help="override earliest period (e.g. 'Fall 2019')")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    profile = dict(PROFILES[args.profile])
    if args.floor:
        profile["floor"] = args.floor
    out_dir = _DATAMART / profile["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    keys = [args.only] if args.only else (catalog_keys() if args.all else BAY_AREA)
    log(f"[{args.profile}] {len(keys)} college(s), >= {profile['floor']} -> {out_dir}")

    done, skipped, failed = [], [], []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not args.headed)
        ctx = b.new_context(accept_downloads=True)
        pg = ctx.new_page()
        pg.set_viewport_size({"width": 1700, "height": 1300})
        canonical = read_canonical_times(pg, profile)
        log(f"Canonical columns ({len(canonical)}): {canonical[0]} .. {canonical[-1]}")
        for n, key in enumerate(keys, 1):
            out = out_dir / f"{key}.csv"
            if out.exists() and out.stat().st_size > 200 and not args.force:
                log(f"[{n}/{len(keys)}] {key}: skip (exists)")
                skipped.append(key)
                continue
            log(f"[{n}/{len(keys)}] {key}: exporting...")
            t0 = time.monotonic()
            try:
                export_college(pg, profile, key, canonical, out)
                log(f"    done in {time.monotonic()-t0:.0f}s")
                done.append(key)
            except Exception as e:
                log(f"    FAILED: {type(e).__name__}: {str(e)[:160]}")
                out.unlink(missing_ok=True)
                (out.with_suffix(".raw.csv")).unlink(missing_ok=True)
                failed.append(key)
        b.close()

    log(f"\nDone: {len(done)} exported, {len(skipped)} skipped, {len(failed)} failed")
    if failed:
        log(f"Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
