"""The response envelope — requirements §4 (epistemic contract) and §5
(response schema) expressed as pure Pydantic types.

The consumer of every tool response is the *model*, so the payload shape is the
behavioral spec. The three obligations are structural here:

- **Bind** — every fact is a ``QualifiedValue``; there is no field on the
  envelope that carries a bare number. To state a datum the model must carry its
  qualifiers, because the datum does not exist in the payload without them.
- **Gate** — a non-``ok`` ``status`` forces ``value=None`` (enforced by a
  validator). Absence is represented, never a zero the model could paper over.
- **Distinguish** — conflatable quantities are separate *named* keys in the
  ``summary``/``row`` dicts (e.g. ``projected_supply`` vs ``actual_awards``);
  the schema never merges them.

Everything is pure (no timestamps, no request ids) so serialization is
byte-reproducible per coordinate.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

# The Gate vocabulary. "ok" carries a value; every other status is an explicit
# epistemic marker with value == None.
Status = Literal["ok", "unavailable", "unknown", "out-of-scope"]


class QualifiedValue(BaseModel):
    """A datum bound to its qualifier triple (source · granularity · vintage).

    Smart-union order keeps an int an int and a float a float, so an openings
    count never silently becomes 340.0. ``status != "ok"`` ⇒ ``value is None``.
    """

    value: Optional[int | float | str] = None
    unit: str = ""
    source: str = ""          # authority id (see provenance.SOURCES) or "derived:<expr>"
    granularity: str = ""
    vintage: str = ""
    status: Status = "ok"

    @model_validator(mode="after")
    def _gate_forces_null(self) -> "QualifiedValue":
        # Gate obligation: a non-ok status can never carry a readable value.
        if self.status != "ok" and self.value is not None:
            self.value = None
        return self

    @classmethod
    def ok(cls, value: int | float | str, *, unit: str = "", source: str = "",
           granularity: str = "", vintage: str = "") -> "QualifiedValue":
        return cls(value=value, unit=unit, source=source,
                   granularity=granularity, vintage=vintage, status="ok")

    @classmethod
    def gated(cls, status: Status, *, unit: str = "", source: str = "",
              granularity: str = "", vintage: str = "") -> "QualifiedValue":
        """An explicit absence marker — value is None by construction."""
        return cls(value=None, unit=unit, source=source, granularity=granularity,
                   vintage=vintage, status=status)


class Coordinate(BaseModel):
    """The scope a response answered at — echoed on every envelope (R2), so the
    provenance triple *is* the conversation's scope memory; no server session."""

    member: str
    member_label: str = ""
    sector: str = ""
    sector_label: str = ""
    region: Optional[str] = None
    soc: Optional[str] = None
    top6: Optional[str] = None


class NextMove(BaseModel):
    """A typed edge of the catalog graph (§5.2) — the server owns the set, the
    model phrases it. Never free text."""

    form: str
    coordinate: Coordinate
    rationale: str = ""


class More(BaseModel):
    """Progressive disclosure (§5.4): the drill is a *scoped re-call*, not a
    cursor and not server state."""

    remaining: int
    drill: NextMove


class Row(BaseModel):
    label: str
    values: dict[str, QualifiedValue] = Field(default_factory=dict)
    # Optional college-grain breakdown (Defect 2): a count is never emitted without a
    # nameable underlying set. Top-N named colleges inline; the row's count field gives the
    # total, so the remainder is disclosed, not hidden.
    roster: list["Row"] = Field(default_factory=list)


class SortAxis(BaseModel):
    """The named measure a ranked response is sorted by — surfaced structurally so
    the axis is never only implied by row order or buried in prose. A fuzzy
    predicate ("attractive") is resolved to one of these named axes and disclosed,
    never collapsed into a hidden composite score."""

    key: str
    label: str
    unit: str = ""
    direction: Literal["higher", "lower"] = "higher"   # which end ranks first


class DataBlock(BaseModel):
    summary: dict[str, QualifiedValue] = Field(default_factory=dict)
    rows: list[Row] = Field(default_factory=list)   # top-N salient only
    more: Optional[More] = None
    sorted_by: Optional[SortAxis] = None   # the named axis rows are ranked by (rankings only)


class Framing(BaseModel):
    """§5.3 — static domain *meaning* + computed epistemic *salience*. Never a
    computed reading of the numbers (that is the model's job, §4.4)."""

    meaning: str = ""
    salience: list[str] = Field(default_factory=list)


class Gate(BaseModel):
    field: str
    marker: Status
    reason: str


class Licensing(BaseModel):
    licensed: list[str] = Field(default_factory=list)
    not_licensed: list[str] = Field(default_factory=list)   # explicit anti-claims
    gates: list[Gate] = Field(default_factory=list)


class ViewLink(BaseModel):
    """The two-window handshake — a deep-link to the corroborating dashboard
    view. ``unavailable`` when the form has no view (§3, non-total mapping)."""

    url: Optional[str] = None
    status: Literal["ok", "unavailable"] = "ok"
    note: str = ""


class SourceRef(BaseModel):
    id: str
    authority: str
    role: str


class Provenance(BaseModel):
    """Response-scope qualifiers, carried ONCE so they survive truncation
    (§4.6): heavyweight authority/vintage strings live here; per-row
    ``QualifiedValue``s carry only the compact source + status."""

    sources: list[SourceRef] = Field(default_factory=list)
    field_authority: dict[str, str] = Field(default_factory=dict)
    scope_granularity: str = ""
    vintages: dict[str, str] = Field(default_factory=dict)


class AnalysisEnvelope(BaseModel):
    """The fixed-arity Tier 1 response. Every slot is obligatory in shape; a
    Gate response leaves ``data`` empty and speaks through ``licensing.gates``
    and ``next_moves``."""

    form: str
    coordinate: Coordinate
    data: DataBlock = Field(default_factory=DataBlock)
    framing: Framing = Field(default_factory=Framing)
    licensing: Licensing = Field(default_factory=Licensing)
    next_moves: list[NextMove] = Field(default_factory=list)
    view_link: ViewLink = Field(default_factory=ViewLink)
    provenance: Provenance = Field(default_factory=Provenance)
