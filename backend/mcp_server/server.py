"""The MCP server — six task-shaped tools + the guided-onboarding prompt.

Tool set (fixed, deterministically ordered — the client caches the tool prefix,
so the order and descriptions are frozen):

  Tier 0   list_scopes · orient
  Tier 1   analyze_gap · analyze_coverage · analyze_pathway · analyze_employer_shed

Each analyze tool wraps its ``forms`` adapter; its description IS its behavioral
spec (the practitioner question + the load-bearing guardrail). The server-level
``instructions`` carry the worldview preamble. Read-only; stateless HTTP.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from mcp_server import catalog as C
from mcp_server import forms as F
from mcp_server import scope as S
from mcp_server.envelope import AnalysisEnvelope
from mcp_server.worldview import START_HERE_PROMPT, WORLDVIEW

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

# The evidence-honest capability landscape (§2) — what is NOT knowable, stated once.
_LIMITS = {
    "wages": "Pooled statewide at the TOP6 program grain for a single cohort — never a specific college's graduates.",
    "spend_vs_gap": "Unavailable — no SWP allocation / NOVA spend data exists in the ontology.",
    "eligibility": "Unavailable — no clock-hour / Workforce-Pell data exists in the ontology.",
    "datamart_suppression": "Not preserved — a DataMart blank is unknown, not zero.",
}


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


class SectorOption(BaseModel):
    sector_id: str
    sector_label: str
    instance: str
    program_count: int = 0   # distinct feeding TOP6 programs the member runs in this sector


class FormInfo(BaseModel):
    form: str
    question: str
    guardrail: str


class OrientResult(BaseModel):
    resolved: bool
    member: str
    member_label: str = ""
    member_kind: str = ""
    region: str = ""
    available_sectors: list[SectorOption] = []
    limits: dict[str, str] = {}
    suggested_first_questions: list[str] = []
    message: str = ""


def _opt(v: str) -> Optional[str]:
    v = (v or "").strip()
    return v or None


# One-sentence routing hints where a tool overlaps another — kept out of the form
# meanings (which are response framing) so they steer tool SELECTION only.
_ROUTING: dict[str, str] = {
    "occupation_profile": ("Reach for this when the question is about one occupation and you "
                           "want the whole picture at once; for a single dimension in depth "
                           "(just the gap, just employers, just feeders), use that specific tool."),
    "gap": ("For one named occupation you want the whole picture on, occupation_profile gives "
            "demand, supply, feeders, and employers in one call; the soc filter here stays "
            "right for a gaps-only view."),
    "pathway": ("For one named occupation you want the whole picture on, occupation_profile "
                "consolidates demand, supply, feeders, and employers in one call."),
    "employer_shed": ("For one named occupation you want the whole picture on, occupation_profile "
                      "consolidates it in one call; this tool stays right for the full employer shed."),
}


def _form_description(form_id: str, *, needs_sector: bool = True) -> str:
    """A form tool's description = its behavioral spec. ``needs_sector`` picks the gate
    line so it always matches the tool's actual schema — occupation_profile takes no
    sector, so its gate must not claim one."""
    f = C.FORMS[form_id]
    gate = ("Needs an established institution and sector first; if that isn't set yet, this "
            "returns an explicit 'not in scope' marker rather than guessing."
            if needs_sector else
            "Needs an established institution — the region is derived from it, and the "
            "occupation (not a sector) is the entry point; an unresolvable institution "
            "returns an explicit 'not in scope' marker, not a guess.")
    parts = [f.question, f.meaning, f"Guardrail: {f.guardrail}"]
    if form_id in _ROUTING:
        parts.append(_ROUTING[form_id])
    parts.append(gate)
    return "\n\n".join(parts)


# ── Tier 0 ────────────────────────────────────────────────────────────────

_LIST_SCOPES_DESC = (
    "List the institutions the system knows — colleges, districts, and consortia — each "
    "with the sectors it is live in, so you can match the practitioner's institution to one "
    "(you resolve the fuzzy name; there is no server-side matcher). Pass a 'filter' substring "
    "(institution or sector name) to get the detailed member×sector rows for the matches.")


@mcp.tool(name="list_institutions", description=_LIST_SCOPES_DESC)
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


_ORIENT_DESC = (
    "Ground yourself in an institution before analyzing: confirm it is known, see "
    "which sectors are live for it, the kinds of questions you can answer about it, "
    "and — honestly — the limits of what the data can say. Do this first, and let it "
    "steer toward high-value questions.")


@mcp.tool(name="institution_overview", description=_ORIENT_DESC)
def orient(member: str, sector: str = "") -> OrientResult:
    port = S.member_portfolio(member)
    if port is None:
        return OrientResult(
            resolved=False, member=member,
            message=(f"No institution matching '{member}'. List the known institutions and "
                     f"match this one to a canonical id (e.g. 'foothill', 'smccd', 'svamp')."))
    return OrientResult(
        resolved=True,
        member=port["member_id"],
        member_label=port["member_label"],
        member_kind=port["member_kind"],
        region=port["region"],
        available_sectors=[SectorOption(sector_id=s["sector_id"], sector_label=s["sector_label"],
                                        instance=s["instance"], program_count=s["program_count"])
                           for s in port["sectors"]],
        limits=_LIMITS,
        suggested_first_questions=[
            f"Which of {port['member_label']}'s sectors has the widest supply–demand gap?",
            "What does one of my programs prepare students for, and who hires for those roles?",
            "How does my institution compare to other colleges covering the same programs?",
        ])


# ── Tier 1 (order frozen for cache stability) ─────────────────────────────

@mcp.tool(name="supply_demand_gaps", description=_form_description("gap"))
def analyze_gap(member: str, sector: str, soc: str = "") -> AnalysisEnvelope:
    return F.analyze_gap(member, sector, soc=_opt(soc))


@mcp.tool(name="program_coverage", description=_form_description("coverage"))
def analyze_coverage(member: str, sector: str) -> AnalysisEnvelope:
    return F.analyze_coverage(member, sector)


@mcp.tool(name="program_pathways", description=_form_description("pathway"))
def analyze_pathway(member: str, sector: str, program: str = "", occupation: str = "") -> AnalysisEnvelope:
    return F.analyze_pathway(member, sector, program=_opt(program), occupation=_opt(occupation))


@mcp.tool(name="regional_employers", description=_form_description("employer_shed"))
def analyze_employer_shed(member: str, sector: str, soc: str = "") -> AnalysisEnvelope:
    return F.analyze_employer_shed(member, sector, soc=_opt(soc))


@mcp.tool(name="occupation_profile", description=_form_description("occupation_profile", needs_sector=False))
def occupation_profile(member: str, occupation: str) -> AnalysisEnvelope:
    return F.occupation_profile(member, occupation)


# ── Prompt ────────────────────────────────────────────────────────────────

@mcp.prompt(name="start-here", description="Guided onboarding: orient to your institution and find high-value questions.")
def start_here() -> str:
    return START_HERE_PROMPT


_START_HERE_DESC = "Guided onboarding: orient to your institution and find high-value questions."


def build_oauth_mcp():
    """A second, OAuth-protected FastMCP with the SAME six tools + prompt — used to
    stand up an OAuth resource-server endpoint (WorkOS as the authorization server)
    alongside the bearer-gated ``mcp``, so we can prove the claude.ai handshake
    without disturbing the working endpoint. Returns None when OAuth env is unset
    (so importing this module never forces OAuth on)."""
    from mcp_server.auth import auth_settings_from_env, verifier_from_env
    settings = auth_settings_from_env()
    if settings is None:
        return None
    m = FastMCP("Kallipolis", instructions=WORLDVIEW, stateless_http=True,
                streamable_http_path="/",
                transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
                auth=settings, token_verifier=verifier_from_env())
    m.tool(name="list_institutions", description=_LIST_SCOPES_DESC)(list_scopes)
    m.tool(name="institution_overview", description=_ORIENT_DESC)(orient)
    m.tool(name="supply_demand_gaps", description=_form_description("gap"))(analyze_gap)
    m.tool(name="program_coverage", description=_form_description("coverage"))(analyze_coverage)
    m.tool(name="program_pathways", description=_form_description("pathway"))(analyze_pathway)
    m.tool(name="regional_employers", description=_form_description("employer_shed"))(analyze_employer_shed)
    m.tool(name="occupation_profile", description=_form_description("occupation_profile", needs_sector=False))(occupation_profile)
    m.prompt(name="start-here", description=_START_HERE_DESC)(start_here)
    return m
