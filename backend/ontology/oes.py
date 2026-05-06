"""
BLS Occupational Employment and Wage Statistics (OEWS) loader.

Provides the canonical industry-occupation mapping for layer 1
(`Employer-[:HIRES_FOR]->Occupation`). The institutional source is the
National Industry-Occupation Matrix published annually by the U.S.
Bureau of Labor Statistics. BLS publishes the matrix at four NAICS
resolutions; we use three (NAICS-2 sector, NAICS-3 subsector, NAICS-4
industry group) bundled in-repo at `data/oes_2023/`.

The descent rule for `oes_socs_for_naics4`: try NAICS-4 first; if BLS
doesn't publish detail at that resolution for the input code, fall back
to NAICS-3, then NAICS-2. This is not a "fallback" pattern — it
matches BLS's own multi-resolution publication shape (their files are
organized that way precisely because their sample doesn't always
support detailed breakouts at the deepest resolution).

Vintage is encoded in the data directory name (`oes_2023/`). A future
upgrade to May 2024 is a deliberate, grep-visible code change: rename
the directory and the path constants below. No silent vintage shifts.

Source: https://www.bls.gov/oes/special-requests/oesm23in4.zip
Reference: https://www.bls.gov/oes/tables.htm

Usage:
    from ontology.oes import oes_socs_for_naics4
    socs = oes_socs_for_naics4("3344")  # Semiconductor manufacturing
    # → list of {"soc": "17-2072", "title": "Electronics Engineers, ...",
    #            "employment": ..., "pct_total": ..., "annual_mean_wage": ...}
"""

from __future__ import annotations

import logging
from pathlib import Path

import openpyxl

logger = logging.getLogger(__name__)

# ── Data paths (vintage encoded in directory name) ────────────────────────

_DATA_DIR = Path(__file__).parent / "data" / "oes_2023"
OES_NAICS2_PATH = _DATA_DIR / "natsector_M2023_dl.xlsx"
OES_NAICS3_PATH = _DATA_DIR / "nat3d_M2023_dl.xlsx"
OES_NAICS4_PATH = _DATA_DIR / "nat4d_M2023_dl.xlsx"

# Education levels excluded from the CTE-eligible SOC pool. CTE programs
# at California community colleges train roles up through associate's
# degrees plus credentialed shorter-term pathways (welding, CNA, CDL).
# Out of scope: roles requiring no formal credentialing (zero CTE
# pathway) and roles requiring a doctoral or professional degree (MD,
# JD, PhD — beyond CCC reach). Master's-required roles ARE retained
# because community colleges feed them via transfer.
#
# Lifted from `enrich.py` so generate.py / enrich.py / oes.py share one
# canonical definition. Keep the frozenset literal in sync with
# OCCUPATIONS_PATH education_level field values.
EXCLUDE_EDUCATION = frozenset({
    "No formal educational credential",
    "Some college, no degree",
    "Doctoral or professional degree",
})

# ── Module-global caches (load-once-per-process) ──────────────────────────

_socs_by_naics2: dict[str, list[dict]] | None = None
_socs_by_naics3: dict[str, list[dict]] | None = None
_socs_by_naics4: dict[str, list[dict]] | None = None


# ── Loaders ───────────────────────────────────────────────────────────────

def _expected_columns() -> set[str]:
    """Columns that MUST be present in every OEWS file. Fail loudly if
    BLS shifts the schema between vintages — silently dropping rows
    would degrade the institutional source without any signal."""
    return {"NAICS", "OCC_CODE", "OCC_TITLE", "O_GROUP",
            "TOT_EMP", "PCT_TOTAL", "A_MEAN"}


def _coerce_numeric(value) -> float | None:
    """BLS suppresses some cells (low employment, confidentiality) as
    '**' or '#'. Return None for non-numeric, otherwise float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _canonicalize_naics(raw, expected_resolution: int) -> list[str]:
    """Canonicalize a raw NAICS cell to a list of canonical keys at the
    expected resolution. Most cells produce a single key; range-encoded
    cells produce multiple.

    BLS encodes NAICS inconsistently across files:
      - `natsector` uses bare 2-digit codes ('11') AND ranges ('31-33',
        '44-45', '48-49') for sectors split across the NAICS standard.
      - `nat3d` and `nat4d` use 6-character zero-padded codes
        ('113000', '113300'). They also publish *aggregate* codes for
        sub-industries combined for sample-size reasons (e.g. '3370A1'
        = "Furniture (3371, 3372 only)"); these are skipped because
        the descent rule already handles their constituent NAICS-4s
        via NAICS-3.

    Range expansion at NAICS-2: "31-33" → ["31", "32", "33"]. This is
    how Manufacturing, Retail, and Transportation are encoded in the
    natsector file. Storing the rows under each constituent NAICS-2
    means the descent lookup can use a uniform `naics4[:2]` key.

    Returns [] if the value can't be canonicalized (logged downstream,
    row skipped).
    """
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    # Pure-digit at the expected resolution (e.g., "11" at NAICS-2,
    # "113" via prefix at NAICS-3, "1133" via prefix at NAICS-4).
    if len(s) == expected_resolution and s.isdigit():
        return [s]
    # 6-char zero-padded form — strip the trailing-zero encoding.
    if len(s) == 6 and s.isdigit():
        return [s[:expected_resolution]]
    # NAICS-2 range encoding ("31-33", "44-45", "48-49"). Only
    # applicable at NAICS-2 — natsector is the only file that uses
    # this encoding.
    if expected_resolution == 2 and "-" in s:
        parts = s.split("-")
        if len(parts) == 2 and all(p.isdigit() and len(p) == 2 for p in parts):
            lo, hi = int(parts[0]), int(parts[1])
            if 0 < lo <= hi < 100:
                return [f"{n:02d}" for n in range(lo, hi + 1)]
    # Aggregate NAICS-4 codes ('3370A1', '4240A2', etc.) — skip; the
    # descent rule already covers them via NAICS-3.
    return []


def _load_oes_file(
    path: Path,
    resolution: int,
) -> dict[str, list[dict]]:
    """Load one OEWS NAICS-resolution file and return
    {naics_canonical: [occupation_row, ...]}.

    Filters rows by O_GROUP == "detailed" (SOC-level rows only) and
    TOT_EMP > 0. Suppressed cells (TOT_EMP is None or non-numeric) are
    skipped.

    Fail-loudly: asserts every column in `_expected_columns()` is
    present in the header. A vintage update that renames or drops a
    column raises immediately rather than degrading data quality
    silently.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"OEWS file not found at {path}. Verify the data is staged "
            f"under backend/ontology/data/oes_2023/. Source zip: "
            f"https://www.bls.gov/oes/special-requests/oesm23in4.zip"
        )

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = {c: i for i, c in enumerate(header)}

    missing = _expected_columns() - cols.keys()
    if missing:
        wb.close()
        raise RuntimeError(
            f"OEWS file {path.name} is missing expected columns "
            f"{sorted(missing)}. Schema may have drifted in this "
            f"vintage; the loader needs updating before proceeding."
        )

    result: dict[str, list[dict]] = {}
    n_kept = 0
    n_skipped_resolution = 0
    n_skipped_suppressed = 0
    n_skipped_not_detailed = 0

    for row in rows:
        if not row:
            continue
        o_group = row[cols["O_GROUP"]]
        if o_group != "detailed":
            n_skipped_not_detailed += 1
            continue

        naics_keys = _canonicalize_naics(row[cols["NAICS"]], resolution)
        if not naics_keys:
            n_skipped_resolution += 1
            continue

        tot_emp = _coerce_numeric(row[cols["TOT_EMP"]])
        if tot_emp is None or tot_emp <= 0:
            n_skipped_suppressed += 1
            continue

        occ = {
            "soc": row[cols["OCC_CODE"]],
            "title": row[cols["OCC_TITLE"]],
            "employment": tot_emp,
            "pct_total": _coerce_numeric(row[cols["PCT_TOTAL"]]) or 0.0,
            "annual_mean_wage": _coerce_numeric(row[cols["A_MEAN"]]),
        }
        # Range-encoded NAICS-2 rows (e.g., "31-33" Manufacturing) are
        # written under each constituent key so the descent lookup can
        # use a uniform `naics4[:2]` key.
        for key in naics_keys:
            result.setdefault(key, []).append(occ)
        n_kept += 1

    wb.close()
    logger.info(
        f"Loaded OEWS {path.name}: {n_kept:,} detailed rows across "
        f"{len(result):,} NAICS-{resolution} codes "
        f"(skipped {n_skipped_not_detailed:,} non-detailed, "
        f"{n_skipped_suppressed:,} suppressed, "
        f"{n_skipped_resolution:,} resolution-mismatch)"
    )
    return result


def _ensure_loaded() -> None:
    """Lazy-load all three resolution files into module globals."""
    global _socs_by_naics2, _socs_by_naics3, _socs_by_naics4
    if _socs_by_naics4 is not None:
        return
    _socs_by_naics2 = _load_oes_file(OES_NAICS2_PATH, resolution=2)
    _socs_by_naics3 = _load_oes_file(OES_NAICS3_PATH, resolution=3)
    _socs_by_naics4 = _load_oes_file(OES_NAICS4_PATH, resolution=4)


# ── Public API ────────────────────────────────────────────────────────────


# OEWS uses code "99" as a cross-cutting government aggregate — "Federal,
# State, and Local Government, excluding State and Local Government Schools
# and Hospitals and the U.S. Postal Service" — published in the natsector
# file. It is BLS's institutional answer for the NAICS-2 "92" Public
# Administration sector that is otherwise absent from the standard
# OEWS National Industry-Occupation Matrix.
#
# Public Admin employers (police, fire, courts, government administration)
# fall through standard NAICS-4 → NAICS-3 → NAICS-2 descent because BLS
# doesn't publish "92" in the natsector file. The fallback rule routes
# them to "99" so their layer 1 pool includes the SOCs they actually
# employ (33-2011 Firefighters, 33-3051 Police, 33-3012 Correctional
# Officers, etc.).
#
# This is not a "fallback to LLM judgment" — it is a routing rule that
# matches BLS's own multi-axis publication structure (NAICS-2 industry
# axis vs. OEWS-specific government axis). The institutional source
# remains OEWS throughout.
_OEWS_GOVERNMENT_CODE = "99"


def oes_socs_for_naics4(naics4: str) -> list[dict]:
    """Return OES industry-occupation rows for a 4-digit NAICS code.

    Descent rule: try NAICS-4 → NAICS-3 → NAICS-2. For NAICS 92
    (Public Administration) specifically, fall through to the OEWS
    cross-cutting government aggregate (code "99") since BLS publishes
    Public Admin under that designation rather than under NAICS-2 92
    in the standard National Industry-Occupation Matrix.

    Each returned row: {soc, title, employment, pct_total,
    annual_mean_wage}. Returns [] only if the input is too short or
    no resolution publishes anything (vanishingly rare).
    """
    if not naics4 or len(naics4) < 4 or not naics4.isdigit():
        return []
    _ensure_loaded()
    rows = _socs_by_naics4.get(naics4)
    if rows:
        return rows
    rows = _socs_by_naics3.get(naics4[:3])
    if rows:
        return rows
    rows = _socs_by_naics2.get(naics4[:2])
    if rows:
        return rows
    # Public Administration (NAICS 92) is not published under NAICS-2
    # in the standard National Industry-Occupation Matrix. Route it to
    # the OEWS cross-cutting government aggregate.
    if naics4[:2] == "92":
        return _socs_by_naics2.get(_OEWS_GOVERNMENT_CODE) or []
    return []


def oes_match_resolution(naics4: str) -> int | str | None:
    """Return the NAICS resolution (2, 3, or 4) at which the input
    matched in the OES descent, or the string "government" if the
    OEWS-99 government-aggregate fallback was used. Returns None if
    no resolution matched. Useful for source attribution in narrative
    and docs.
    """
    if not naics4 or len(naics4) < 4 or not naics4.isdigit():
        return None
    _ensure_loaded()
    if _socs_by_naics4.get(naics4):
        return 4
    if _socs_by_naics3.get(naics4[:3]):
        return 3
    if _socs_by_naics2.get(naics4[:2]):
        return 2
    if naics4[:2] == "92" and _socs_by_naics2.get(_OEWS_GOVERNMENT_CODE):
        return "government"
    return None


# ── Eager load on module import ───────────────────────────────────────────
#
# Lazy-loading the OEWS files via _ensure_loaded() at first call created
# a race condition under FastAPI's threaded sync handlers: when multiple
# requests hit the API simultaneously after a backend restart (typical
# during deploy or after OOM-recovery), each thread saw the module
# globals as unset and started loading the same Excel files in parallel.
# A single load is ~5-10s of openpyxl parsing per file (3 files); the
# race multiplied the work, producing 60s+ cold-start timeouts on the
# first batch of requests after every deploy.
#
# Eager-loading at module import resolves the race entirely: imports
# block on the load, but module imports happen at process startup
# before uvicorn accepts connections, so the cost is invisible to
# users. Backend boot time goes from ~2s to ~12s; first request after
# boot is fast.
#
# The try/except keeps this safe in environments where the OEWS data
# files might not be staged (tests, fresh dev clones). Failure here
# falls back to the original lazy-on-first-call behavior, with the
# original race risk intact in those edge cases.
#
# This is a band-aid. The architectural fix is to materialize OEWS
# data into the graph as NAICS nodes with HAS_INDUSTRY_PRESENCE edges
# to Occupation, removing this module from the API request path
# entirely. When that lands, this eager-load (and most of this file's
# import-time impact) disappears.
try:
    _ensure_loaded()
    logger.info("OEWS eager-load complete (NAICS-2/3/4 ready)")
except Exception as e:
    logger.warning(
        f"OEWS eager-load failed at import: {e}. "
        f"Falling back to lazy-load on first request."
    )
