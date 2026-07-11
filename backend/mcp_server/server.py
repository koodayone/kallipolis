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

from mcp.server.fastmcp import FastMCP

from mcp_server import catalog as C
from mcp_server import forms as F
from mcp_server import scope as S
from mcp_server.envelope import AnalysisEnvelope
from mcp_server.worldview import START_HERE_PROMPT, WORLDVIEW

# streamable_http_path="/" so the app serves at its mount root: mounted at
# "/mcp" in main.py, the MCP endpoint is exactly /mcp (not /mcp/mcp).
mcp = FastMCP("Kallipolis", instructions=WORLDVIEW, stateless_http=True,
              streamable_http_path="/")

_SCOPE_KEYS = ("id", "member_id", "member_label", "member_kind", "sector_id", "sector_label")

# The evidence-honest capability landscape (§2) — what is NOT knowable, stated once.
_LIMITS = {
    "wages": "Pooled statewide at the TOP6 program grain for a single cohort — never a specific college's graduates.",
    "spend_vs_gap": "Unavailable — no SWP allocation / NOVA spend data exists in the ontology.",
    "eligibility": "Unavailable — no clock-hour / Workforce-Pell data exists in the ontology.",
    "datamart_suppression": "Not preserved — a DataMart blank is unknown, not zero.",
}


def _opt(v: str) -> Optional[str]:
    v = (v or "").strip()
    return v or None


def _form_description(form_id: str) -> str:
    f = C.FORMS[form_id]
    return (f"{f.question}\n\n{f.meaning}\n\nGuardrail: {f.guardrail}\n\n"
            f"Requires a resolved (member, sector) coordinate — call orient first if unsure; "
            f"an unresolved coordinate returns an explicit gate, not a guess.")


# ── Tier 0 ────────────────────────────────────────────────────────────────

@mcp.tool(description=(
    "Tier 0 — list the canonical member×sector universe the system knows. "
    "Match the user's institution to a canonical member id (the consumer, you, "
    "resolves fuzzy names — there is no server-side matcher), then call orient. "
    "Optional 'filter' substring narrows by member or sector name/id."))
def list_scopes(filter: str = "") -> dict:
    f = filter.strip().lower()
    scopes = []
    for e in S.scope_catalog():
        hay = f"{e['member_id']} {e['member_label']} {e['sector_id']} {e['sector_label']}".lower()
        if not f or f in hay:
            scopes.append({k: e[k] for k in _SCOPE_KEYS})
    return {"count": len(scopes), "scopes": scopes}


@mcp.tool(description=(
    "Tier 0 — orient to an institution: validate the member, present the sectors "
    "that are live for it, the four analytical forms available, and — honestly — "
    "the limits of what the data can assert. Call this before analysis to ground "
    "the scope and steer toward high-value questions."))
def orient(member: str, sector: str = "") -> dict:
    sects = S.sectors_for_member(member)
    if not sects:
        return {
            "resolved": False,
            "member": member,
            "message": (f"No member '{member}' in the universe. Call list_scopes and match "
                        f"the institution to a canonical member id (e.g. 'foothill', 'smccd', 'svamp')."),
        }
    head = sects[0]
    return {
        "resolved": True,
        "member": head["member_id"],
        "member_label": head["member_label"],
        "member_kind": head["member_kind"],
        "available_sectors": [{"sector_id": e["sector_id"], "sector_label": e["sector_label"],
                               "instance": e["id"]} for e in sects],
        "forms": [{"form": fid, "question": C.FORMS[fid].question,
                   "guardrail": C.FORMS[fid].guardrail} for fid in C.FORMS],
        "limits": _LIMITS,
        "suggested_first_questions": [
            f"Where are the biggest supply–demand gaps for {head['member_label']} in a sector?",
            "Which colleges cover the in-demand occupations in that sector?",
            "Who are the regional employers to convene around a gapped occupation?",
        ],
    }


# ── Tier 1 (order frozen for cache stability) ─────────────────────────────

@mcp.tool(description=_form_description("gap"))
def analyze_gap(member: str, sector: str, soc: str = "") -> AnalysisEnvelope:
    return F.analyze_gap(member, sector, soc=_opt(soc))


@mcp.tool(description=_form_description("coverage"))
def analyze_coverage(member: str, sector: str) -> AnalysisEnvelope:
    return F.analyze_coverage(member, sector)


@mcp.tool(description=_form_description("pathway"))
def analyze_pathway(member: str, sector: str, program: str = "", occupation: str = "") -> AnalysisEnvelope:
    return F.analyze_pathway(member, sector, program=_opt(program), occupation=_opt(occupation))


@mcp.tool(description=_form_description("employer_shed"))
def analyze_employer_shed(member: str, sector: str, soc: str = "") -> AnalysisEnvelope:
    return F.analyze_employer_shed(member, sector, soc=_opt(soc))


# ── Prompt ────────────────────────────────────────────────────────────────

@mcp.prompt(name="start-here", description="Guided onboarding: orient to your institution and find high-value questions.")
def start_here() -> str:
    return START_HERE_PROMPT
