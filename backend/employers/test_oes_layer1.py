"""C13 rationality harness — domain-signature assertions on the
post-migration `occupations` field.

Ports the 12-employer test set from /tmp/proposed_arch_experiment.py
to a deterministic, repo-tested artifact. Reads
`employers/employers.json` directly; no Gemini calls, no Neo4j.
The harness's job is to catch architectural regressions in the
NAICS-OES anchoring of layer 1: if a future change re-introduces
the regional CTE-pathway pool or breaks the descent rule, these
assertions fail loudly.

Each test employer is associated with a *domain-signature SOC* —
the institutionally-canonical occupation code that an industry-
anchored pool MUST surface for that employer's industry. The
pre-C13 LLM-only pool failed each of these signatures (Otay Water
without water/wastewater operators, Cisco without software
developers, etc.). Post-C13, the OES NAICS-bounded pool surfaces
them deterministically.

The `expected_any_of` semantics tolerates SOC version drift —
when BLS rolls a new SOC vintage, an employer's "best signature
SOC" may shift between adjacent codes (e.g., 15-1252 ↔ 15-1251).
The set-overlap check is robust to that.

NAICS 92 employers (e.g., Shasta County Fire Department) route to
BLS's OEWS-99 cross-cutting government aggregate rather than the
NAICS-2 axis (where Public Administration is absent in the standard
National Industry-Occupation Matrix). The fix at oes.py: descent
checks for naics4[:2] == "92" and falls through to the "99" pool,
which carries 33-2011 Firefighters, 33-3051 Police, 33-3012
Correctional Officers, etc. Public Admin employers therefore get
real institutionally-sourced layer 1 pools and are not silently
excluded from the partnerships landscape.

Coverage:
  - 12 SWP-sector employers, each tested for at least one canonical
    industry-signature SOC in their post-migration occupations list
    (Otay Water → 51-8031; Baker Electric → 47-2111; Cisco → 15-1252;
    Pentair, UPS, Paychex, SDUSD, Southern Glazer's, Sharp HealthCare,
    Halozyme, CPK each have an `expected_any_of` SOC set)
  - NAICS 92 (Shasta County Fire) → Firefighters (33-2011) via the
    OEWS-99 government-aggregate routing; this is the institutional
    coverage of Public Admin employers, not a fallback
  - All occupations match canonical \\d{2}-\\d{4} SOC format
  - Every promoted record has naics4 set after C13 backfill
  - Every record's occupations list is 1-5 entries (or empty per C12)

Run:
    python -m pytest backend/employers/test_oes_layer1.py -v
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"


# ── Domain-signature contract ─────────────────────────────────────────────
#
# Each entry: (employer_name, expected_any_of_socs, why)
#
# expected_any_of is a set — the assertion passes if the post-migration
# occupations list intersects the set non-emptily. Set semantics tolerate
# adjacent-SOC drift across BLS vintages.
#
# A None expected_any_of means "the employer's NAICS is uncovered by
# OEWS national industry matrix and the migration correctly produces
# empty occupations" (NAICS 92 / Public Administration).

DOMAIN_SIGNATURES: list[tuple[str, set[str] | None, str]] = [
    ("Otay Water District", {"51-8031"},
     "water utility (NAICS 2213) → water/wastewater operators"),
    ("Baker Electric", {"47-2111"},
     "electrical contractor (NAICS 2382) → electricians"),
    ("Cisco Systems", {"15-1252", "15-1251"},
     "communications equipment / software (NAICS 3342) → software developers"),
    ("Pentair Electronic Packaging",
     {"51-4121", "51-4041", "51-9161", "51-1011", "51-2090", "51-9061",
      "17-2141", "49-9041"},
     "metal-enclosure / industrial-machinery manufacturer (NAICS 3332) → "
     "welders, machinists, CNC operators, production supervisors, "
     "industrial machinery mechanics, mechanical engineers, or assemblers"),
    ("UPS", {"53-3032", "53-7065", "43-5061", "43-5052", "53-7062"},
     "logistics/courier (NAICS 4921) → drivers / shipping clerks / handlers"),
    ("Paychex", {"43-3051", "13-2011", "43-3031"},
     "payroll services (NAICS 5412 area) → payroll/timekeeping clerks "
     "or accountants"),
    ("San Diego Unified School District", {"25-2021", "25-2031", "53-3052"},
     "K-12 district (NAICS 6111) → teachers or school bus drivers"),
    ("Southern Glazer's Wine & Spirits", {"53-3032", "41-4012", "53-7062", "53-7065"},
     "beverage wholesaler (NAICS 4248) → drivers / wholesale sales reps"),
    ("Sharp HealthCare", {"29-1141", "29-2061", "29-2055"},
     "general hospital (NAICS 6221) → registered nurses / LPNs"),
    ("Halozyme Therapeutics", {"19-1042", "19-4021", "19-1029"},
     "biotech R&D (NAICS 5417 / 3254) → medical scientists or biological "
     "technicians"),
    ("Shasta County Fire Department", {"33-2011", "33-1021", "33-2021"},
     "Public Administration (NAICS 9224) → routes to OEWS-99 government "
     "aggregate, surfacing firefighter / firefighting-supervisor SOCs"),
    ("California Pizza Kitchen", {"35-1012", "35-2014", "35-3031"},
     "restaurant chain (NAICS 7225) → food service supervisors / cooks / "
     "servers"),
]


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def employers_by_name() -> dict[str, dict]:
    with open(EMPLOYERS_PATH) as f:
        records = json.load(f)
    return {r["name"]: r for r in records}


# ── Domain-signature tests (parametrized) ──────────────────────────────────


@pytest.mark.parametrize(
    "name,expected_any_of,why",
    DOMAIN_SIGNATURES,
    ids=[t[0] for t in DOMAIN_SIGNATURES],
)
def test_domain_signature(
    name: str,
    expected_any_of: set[str] | None,
    why: str,
    employers_by_name: dict[str, dict],
):
    emp = employers_by_name.get(name)
    assert emp is not None, (
        f"{name!r} not found in employers.json — the rationality harness "
        f"is keyed to specific employers; if a region's data set has "
        f"shifted, update DOMAIN_SIGNATURES with the new canonical names"
    )
    socs = set(emp.get("occupations") or [])
    if expected_any_of is None:
        # NAICS 92 / Public Admin: correct behavior is empty occupations.
        assert socs == set(), (
            f"{name} ({why}): expected empty occupations (Public Admin "
            f"uncovered by OEWS), got {socs}"
        )
    else:
        assert socs & expected_any_of, (
            f"{name} ({why}): expected at least one of "
            f"{sorted(expected_any_of)} in occupations, got {sorted(socs)}"
        )


# ── Aggregate invariants ──────────────────────────────────────────────────


_SOC_RE = re.compile(r"^\d{2}-\d{4}$")


def test_occupations_in_canonical_format(employers_by_name):
    """Every SOC in every employer's occupations list matches the
    canonical \\d{2}-\\d{4} pattern. Catches stale / malformed values
    that might survive a partial migration write."""
    failures = []
    for name, emp in employers_by_name.items():
        for soc in emp.get("occupations") or []:
            if not (isinstance(soc, str) and _SOC_RE.match(soc)):
                failures.append(f"{name}: non-canonical SOC {soc!r}")
    assert not failures, "\n".join(failures[:20])


def test_promoted_records_have_naics4(employers_by_name):
    """Every record that's been through enrichment AND will be loaded
    into Neo4j (`enrichment_promoted=True`) must have a NAICS-4 set
    after C13. Records with missing naics4 are the symptom that the
    historical backfill failed for them — they need attention."""
    missing = [
        e["name"] for e in employers_by_name.values()
        if e.get("enrichment_promoted") is True and not e.get("naics4")
    ]
    assert not missing, (
        f"{len(missing)} promoted employers without naics4 — backfill "
        f"failed for these. Examples: {missing[:5]}"
    )


def _is_loadable(emp: dict) -> bool:
    """Mirrors employers/load.py:_is_loadable. Bound assertions apply
    only to loadable records — deferred records (attempted but not
    verified) are excluded from Neo4j and may carry legacy data the
    migration intentionally didn't touch."""
    if not emp.get("enrichment_attempted"):
        return True
    if not emp.get("identity_verified"):
        return False
    return emp.get("enrichment_promoted") is True


def test_occupations_within_size_bound(employers_by_name):
    """Per the converged Pass 3 prompt, every loadable employer's
    occupations list is either empty (C12-aligned exclusion) or 1–5
    SOCs. Catches both prompt drift and validator regression. Bound
    applies to loadable records only."""
    failures = []
    for name, emp in employers_by_name.items():
        if not _is_loadable(emp):
            continue
        n = len(emp.get("occupations") or [])
        if n > 5:
            failures.append(f"{name}: {n} occupations (max 5)")
        # n == 0 is acceptable per C12
    assert not failures, "\n".join(failures[:20])


# ── Coverage summary (informational) ───────────────────────────────────────


def test_coverage_summary(employers_by_name, capsys):
    """Print a summary so the operator can eyeball the migration's
    rationality coverage. Always passes."""
    n = len(employers_by_name)
    with_naics4 = sum(1 for e in employers_by_name.values() if e.get("naics4"))
    with_occs = sum(1 for e in employers_by_name.values()
                    if (e.get("occupations") or []))
    promoted = sum(1 for e in employers_by_name.values()
                   if e.get("enrichment_promoted") is True)
    legacy = sum(1 for e in employers_by_name.values()
                 if not e.get("enrichment_attempted"))
    with capsys.disabled():
        print(f"\nC13 layer 1 coverage:")
        print(f"  Total records:           {n}")
        print(f"    enrichment_promoted:   {promoted}")
        print(f"    legacy (not attempted): {legacy}")
        print(f"  With naics4:             {with_naics4} ({100*with_naics4/n:.1f}%)")
        print(f"  With non-empty occs:     {with_occs} ({100*with_occs/n:.1f}%)")
