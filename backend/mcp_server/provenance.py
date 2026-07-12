"""Provenance attachment — the data side of the Bind obligation.

Every fact the envelope carries gets its authority (WHO), granularity (WHAT
scope) and vintage (as of WHEN) from here. The authority is read from the
engine's own provenance substrate (``partnerships.lens.FIELD_AUTHORITY`` /
``SOURCES``) and the COE vintages from ``ontology.supply`` — never invented. If
this module cannot name a source for a field, that is a bug to fix *here*, not a
value to guess in a form adapter.
"""
from __future__ import annotations

from typing import Iterable, Optional

from ontology.supply import COE_DEMAND_VINTAGE
from partnerships.lens import FIELD_AUTHORITY as _LENS_FIELD_AUTHORITY
from partnerships.lens import SOURCES as _LENS_SOURCES

from mcp_server.envelope import Provenance, QualifiedValue, SourceRef, Status

# The BLS OEWS staffing matrix carries no year column into the graph; its vintage
# is the matrix identity, stated rather than faked with a spurious year.
OES_VINTAGE = "BLS OEWS Industry-Occupation staffing matrix"

# The envelope's fact vocabulary → institutional authority id. Reuses the
# engine's field→authority map verbatim and extends it to the envelope's named
# keys. Ids index ``partnerships.lens.SOURCES`` (coe | datamart | graph_bls | onet).
AUTHORITY_BY_FIELD: dict[str, str] = {
    **_LENS_FIELD_AUTHORITY,
    # demand — COE regional
    "annual_openings": "coe",
    "annual_wage": "coe",
    "growth_rate": "coe",
    "regional_employment": "coe",
    "typical_education": "coe",     # BLS entry-level education, carried in the COE demand file
    # supply — the Distinguish pair, kept as deliberately separate keys. Both are now
    # DataMart completions (COE's supply IS DataMart CO-approved completions); they differ
    # by window: projected_supply = 3-yr avg (COE's annual-projection method), latest = 1 yr.
    "projected_supply": "datamart",     # 3-yr-avg DataMart completions, COE annual-projection method
    "latest_year_supply": "datamart",   # the single most recent year — a trend complement
    "actual_awards": "datamart",   # DataMart actual completions (ground truth)
    "enrollment": "datamart",
    # coverage
    "coverage": "datamart",
    "course_count": "datamart",
    # wage outcomes — pooled statewide TOP6 cohort
    "wage_before": "datamart",
    "wage_after_2": "datamart",
    "wage_after_5": "datamart",
    # employer shed
    "employer_relevance": "graph_bls",
    "candidate_employers": "graph_bls",
    # computed
    "gap": "derived",              # regional openings − institutional projected completions
}


def authority_of(field: str) -> str:
    """The source id for a field. ``'derived'`` for computed values; ``''`` means
    unmapped — surfaced as a bug rather than papered over."""
    return AUTHORITY_BY_FIELD.get(field, "")


def default_vintage(field: str) -> str:
    """The file-level vintage where it is a fixed publication fact. Data-derived
    vintages (award-year window, supply window, wage cohort) are passed per call —
    including supply, which is now a DataMart completions window, not the COE file."""
    src = AUTHORITY_BY_FIELD.get(field)
    if src == "coe":
        return COE_DEMAND_VINTAGE
    if src == "graph_bls":
        return OES_VINTAGE
    return ""  # datamart awards/enrollment/wage carry a data-derived window


def q(field: str, value, *, granularity: str, unit: str = "",
      vintage: Optional[str] = None, status: Status = "ok") -> QualifiedValue:
    """Build a QualifiedValue with source (never invented) + vintage attached.

    Pass an explicit ``vintage`` for data-derived windows (awards/wage);
    otherwise the file-level default is used. A non-ok ``status`` yields an
    explicit epistemic marker (value None)."""
    v = vintage if vintage is not None else default_vintage(field)
    src = authority_of(field)
    if status != "ok":
        return QualifiedValue.gated(status, unit=unit, source=src, granularity=granularity, vintage=v)
    return QualifiedValue.ok(value, unit=unit, source=src, granularity=granularity, vintage=v)


def source_refs(field_names: Iterable[str]) -> list[SourceRef]:
    """The distinct institutional sources behind a set of fields, id-sorted."""
    ids = {authority_of(f) for f in field_names}
    ids -= {"", "derived"}
    out: list[SourceRef] = []
    for sid in sorted(ids):
        ref = _LENS_SOURCES.get(sid)
        if ref is not None:
            out.append(SourceRef(id=ref.id, authority=ref.authority, role=ref.role))
    return out


def build_provenance(field_names: Iterable[str], *, scope_granularity: str,
                     vintages: dict[str, str]) -> Provenance:
    """The response-scope provenance block — carried once, survives truncation."""
    names = sorted(set(field_names))
    return Provenance(
        sources=source_refs(names),
        field_authority={f: authority_of(f) for f in names if authority_of(f)},
        scope_granularity=scope_granularity,
        vintages=dict(sorted(vintages.items())),
    )
