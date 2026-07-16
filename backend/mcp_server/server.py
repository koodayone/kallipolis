"""The MCP server — the coordinate-algebra verbs + the list helper + the onboarding prompt.

Tool set (the client caches the tool prefix, so order and descriptions are frozen):

  Verbs    orient · navigate · crosswalk · compare · sweep(reserved) — the coordinate-algebra surface
  Helper   list_institutions — the registry the model resolves a fuzzy name against before orienting

  The eleven task-shaped tools are retired: every view they served is now reached by a verb whose
  coordinate carries the entity/lens it dispatches on (navigate re-materializes a sector, an occupation,
  or the gaps/employers/greenfield/coverage lenses; crosswalk traverses a program↔occupation; orient
  returns the member portfolio). The verbs dispatch into the SAME `forms` functions the tools called —
  one kernel beneath, five verbs above.

Each tool's description IS its behavioral spec: the shared ``DOCTRINE`` (voice +
the intent-gated reading rules + the navigation offer) prepended to the tool's own
spec — for an analyze tool, its practitioner question + load-bearing guardrail.
Prepending DOCTRINE to every description puts the reading contract on the one
channel every client injects; the server-level ``instructions`` (advisory) carry
the same doctrine as a preamble but load-bear nothing. Read-only; stateless HTTP.
"""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from mcp_server import catalog as C
from mcp_server import forms as F
from mcp_server import scope as S
from mcp_server.compare import REGISTRY as _COMPARE_REGISTRY
from mcp_server.envelope import AnalysisEnvelope
from mcp_server.worldview import DOCTRINE, START_HERE_PROMPT, WORLDVIEW

# streamable_http_path="/" so the app serves at its mount root: mounted at
# "/mcp" in main.py, the MCP endpoint is exactly /mcp (not /mcp/mcp).
#
# transport_security: FastMCP's DNS-rebinding protection defaults to trusting only
# localhost, so it 421s the real Host header when the server runs behind Caddy
# (api.kallipolis.us). The endpoint is bearer-gated by the reverse proxy — a
# trusted boundary — and read-only, so the protection is redundant here; disable
# it rather than pin a brittle proxy-host allow-list.
mcp = FastMCP("Kallipolis", instructions=WORLDVIEW, stateless_http=True,
              streamable_http_path="/",
              transport_security=TransportSecuritySettings(
                  enable_dns_rebinding_protection=False))

_SCOPE_KEYS = ("id", "member_id", "member_label", "member_kind", "sector_id", "sector_label")


# ── Tier 0 structured response models (so the model receives structuredContent,
#    not just JSON-as-text — parity with the Tier 1 AnalysisEnvelope) ──

class ScopeEntry(BaseModel):
    id: str
    member_id: str
    member_label: str
    member_kind: str
    sector_id: str
    sector_label: str


class InstitutionSummary(BaseModel):
    member_id: str
    member_label: str
    member_kind: str
    sectors: list[str] = []   # sector labels this institution is live in


class ScopeList(BaseModel):
    count: int
    institutions: list[InstitutionSummary] = []   # default (no filter): one row per institution
    scopes: list[ScopeEntry] = []                 # filtered: detailed member×sector rows


class FormInfo(BaseModel):
    form: str
    question: str
    guardrail: str


def _opt(v: str) -> Optional[str]:
    v = (v or "").strip()
    return v or None


def _prime(desc: str) -> str:
    """Prepend the shared DOCTRINE to a tool description. Tool descriptions are the
    one priming channel every client injects, so this is where the reading contract
    must ride to reach the model on every call — not the advisory ``instructions``."""
    return f"{DOCTRINE}\n\n{desc}"


def _compare_description() -> str:
    """The compare tool's description — the criteria MENU is generated from the REGISTRY, so the
    surface auto-updates the moment a criterion or unit type is added (data, not code)."""
    f = C.FORMS["compare"]
    menu = "\n".join(f"  {ut}s — rank by: " + ", ".join(crits)
                     for ut, crits in _COMPARE_REGISTRY.items())
    parts = [
        f.question, f.meaning, f"Criteria you can rank by:\n{menu}", f"Guardrail: {f.guardrail}",
        ("Reach for this to RANK a set of analogous units against each other by a named measure — a "
         "member's programs, the sector's occupations, or the region's colleges (the unit_type). Map a "
         "loose ask ('which occupations are attractive') to a named criterion, rank by it, and say "
         "which; typically after navigate has framed the sector."),
        ("Needs an established institution and sector; an unknown unit_type or criterion returns the "
         "valid menu rather than guessing."),
    ]
    return _prime("\n\n".join(parts))


# ── Tier 0 ────────────────────────────────────────────────────────────────

_LIST_SCOPES_DESC = (
    "List the institutions the system knows — colleges, districts, and consortia — each "
    "with the sectors it is live in, so you can match the practitioner's institution to one "
    "(you resolve the fuzzy name; there is no server-side matcher). Pass a 'filter' substring "
    "(institution or sector name) to get the detailed member×sector rows for the matches.")


@mcp.tool(name="list_institutions", description=_prime(_LIST_SCOPES_DESC))
def list_scopes(filter: str = "") -> ScopeList:
    f = filter.strip().lower()
    if not f:
        # Default: one row per institution (id/label/kind + its live sectors) — enough to
        # resolve a fuzzy name, ~8x lighter than the full member×sector cross-product. The
        # detailed rows are reachable via a filter.
        by_member: dict[str, dict] = {}
        for e in S.scope_catalog():
            m = by_member.setdefault(e["member_id"], {
                "member_id": e["member_id"], "member_label": e["member_label"],
                "member_kind": e["member_kind"], "sectors": set()})
            m["sectors"].add(e["sector_label"])
        insts = sorted(
            (InstitutionSummary(member_id=m["member_id"], member_label=m["member_label"],
                                member_kind=m["member_kind"], sectors=sorted(m["sectors"]))
             for m in by_member.values()),
            key=lambda i: (i.member_kind, i.member_id))
        return ScopeList(count=len(insts), institutions=insts)
    scopes = [ScopeEntry(**{k: e[k] for k in _SCOPE_KEYS}) for e in S.scope_catalog()
              if f in f"{e['member_id']} {e['member_label']} {e['sector_id']} {e['sector_label']}".lower()]
    return ScopeList(count=len(scopes), scopes=scopes)


# ── compare — the vary/by verb ───────────────────────────────────────────
# (`compare`'s form function backs the ranking menu; the other form functions in `forms`
# back the navigate/crosswalk/orient dispatch — the legacy per-task tools are retired.)

@mcp.tool(name="compare", description=_compare_description())
def compare(member: str, unit_type: str = "program", criterion: str = "",
            sector: str = "") -> AnalysisEnvelope:
    return F.compare(member, unit_type=unit_type, criterion=criterion, sector=sector)


# ── The coordinate-algebra verbs (the surface; the task-shaped tools are retired) ──
# One Coordinate ⟨member | sector | entity | lens | vintage | predicate-version⟩, five verbs. Each
# verb takes a coordinate and dispatches into the form functions in `forms` — one kernel beneath,
# five verbs above. `compare` (above) is already the verb; `sweep` is reserved.

_SOC_RE = re.compile(r"^\d{2}-\d{4}$")   # an occupation entity, e.g. 51-4041

_ORIENT_VERB_DESC = (
    "orient(member) — fix the institutional frame before analyzing: resolve the institution, derive "
    "its region, and return the top of the descent — the member's whole portfolio, one row per sector "
    "with demand, supply, share, and gap. Start here, then navigate in.")
_NAVIGATE_DESC = (
    "navigate(to) — move within the institution's hierarchy: set or change the SECTOR, the ENTITY (an "
    "occupation SOC), or the LENS (gaps · employers · greenfield · coverage), and get the canonical view "
    "at the resulting coordinate. navigate(sector) is the sector view; navigate(entity=<soc>) the "
    "occupation; navigate(lens=gaps|employers|greenfield|coverage) re-materializes the current address "
    "through another face (coverage = which of the member's colleges cover which programs).")
_CROSSWALK_DESC = (
    "crosswalk(across) — traverse the TOP→CIP→SOC bridge in either direction: a PROGRAM → the "
    "occupations it prepares students for, or an OCCUPATION → the programs regionwide that feed it. "
    "Pass the program (TOP6), the occupation (SOC), or a coordinate's entity= directly. "
    "The mapping is lossy and many-to-many by design; the fan-out is surfaced, never collapsed.")
_SWEEP_DESC = (
    "sweep(over: vintage) — RESERVED. The time-series verb the coordinate algebra predicts: vary the "
    "vintage while holding the rest of the coordinate fixed. Specified but not yet built — do not "
    "simulate a time series by looping other verbs.")


@mcp.tool(name="orient", description=_prime(_ORIENT_VERB_DESC))
def orient_v(member: str) -> AnalysisEnvelope:
    return F.member_portfolio(member)


@mcp.tool(name="navigate", description=_prime(_NAVIGATE_DESC))
def navigate(member: str, sector: str = "", entity: str = "", lens: str = "") -> AnalysisEnvelope:
    entity, lens = entity.strip(), lens.strip().lower()
    is_soc = bool(_SOC_RE.match(entity))
    if lens == "greenfield":
        return F.unmet_demand(member)
    if lens == "employers":
        return F.analyze_regional_employers(member, sector, soc=_opt(entity if is_soc else ""))
    if lens == "coverage":
        return F.analyze_coverage(member, sector)            # which colleges cover which programs
    if is_soc and not sector:
        return F.occupation_profile(member, entity)          # sector-agnostic occupation view
    if is_soc:
        return F.analyze_gap(member, sector, soc=entity)      # the occupation within its sector
    if lens == "gaps":
        return F.analyze_gap(member, sector)
    return F.sector_overview(member, sector)                  # the sector's canonical view


@mcp.tool(name="crosswalk", description=_prime(_CROSSWALK_DESC))
def crosswalk(member: str, sector: str, program: str = "", occupation: str = "",
              entity: str = "") -> AnalysisEnvelope:
    # `entity` is the coordinate's dispatch key: a SOC crosswalks as an occupation, a TOP6 as a program.
    entity = entity.strip()
    if entity and _SOC_RE.match(entity):
        occupation = occupation or entity
    elif entity:
        program = program or entity
    return F.analyze_pathway(member, sector, program=_opt(program), occupation=_opt(occupation))


@mcp.tool(name="sweep", description=_prime(_SWEEP_DESC))
def sweep(member: str, sector: str = "") -> AnalysisEnvelope:
    return S.gate_envelope("sweep", member, sector, marker="out-of-scope",
                           reason="sweep(over: vintage) is a reserved verb — specified but not yet built.")


# ── Prompt ────────────────────────────────────────────────────────────────

@mcp.prompt(name="start-here", description="Guided onboarding: orient to your institution and find high-value questions.")
def start_here() -> str:
    return START_HERE_PROMPT


_START_HERE_DESC = "Guided onboarding: orient to your institution and find high-value questions."


def build_oauth_mcp():
    """A second, OAuth-protected FastMCP with the SAME surface (the five verbs + list helper +
    prompt) — used to stand up an OAuth resource-server endpoint (WorkOS as the authorization
    server) alongside the bearer-gated ``mcp``, so we can prove the claude.ai handshake without
    disturbing the working endpoint. Returns None when OAuth env is unset (so importing this
    module never forces OAuth on)."""
    from mcp_server.auth import auth_settings_from_env, verifier_from_env
    settings = auth_settings_from_env()
    if settings is None:
        return None
    m = FastMCP("Kallipolis", instructions=WORLDVIEW, stateless_http=True,
                streamable_http_path="/",
                transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
                auth=settings, token_verifier=verifier_from_env())
    m.tool(name="list_institutions", description=_prime(_LIST_SCOPES_DESC))(list_scopes)
    m.tool(name="orient", description=_prime(_ORIENT_VERB_DESC))(orient_v)
    m.tool(name="navigate", description=_prime(_NAVIGATE_DESC))(navigate)
    m.tool(name="crosswalk", description=_prime(_CROSSWALK_DESC))(crosswalk)
    m.tool(name="compare", description=_compare_description())(compare)
    m.tool(name="sweep", description=_prime(_SWEEP_DESC))(sweep)
    m.prompt(name="start-here", description=_START_HERE_DESC)(start_here)
    return m
