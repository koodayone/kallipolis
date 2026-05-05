"""Two-pass website-grounded employer enrichment.

Replaces the populate_description + classify_employers chain with a
single coherent module that treats the website as the canonical
evidentiary substrate for everything we know about an employer.

Pass 1 — Identity probe:
  Read the candidate URL and decide whether it represents this
  employer. Binary match/mismatch with a verbatim evidence quote.
  Strict: a wrong URL is worse than dropping a legitimate employer.
  Mismatch triggers one auto-retry via Gemini Search grounding; if the
  retry returns the same URL or REMOVE, the employer is dropped to
  dropped.jsonl. No human-review queue.

Pass 2 — Enrichment:
  For verified employers, read the same page and extract description
  (60-120 words, grounded), occupations (3-8 SOC codes from the
  regional list), and swp_sector (one of 12). Schema-enforced.
  Fetch failures leave shadow fields absent for next-run retry.

Shadow fields (cutover happens manually after audit):
  identity_verified: absent | true     (canonical, gates dataset membership)
  _description:      <string>          (shadow for description)
  _occupations:      <list[str]>       (shadow for occupations)
  _swp_sector:       <string>          (shadow for swp_sectors[0])

Usage:
    python3 -m employers.enrich --dry-run --limit 5
    python3 -m employers.enrich --limit 50
    python3 -m employers.enrich --region SCC
    python3 -m employers.enrich --concurrency 10
    python3 -m employers.enrich --skip-enrich   # probe-only
    python3 -m employers.enrich --skip-probe    # enrich-only (assumes verified)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
OCCUPATIONS_PATH = _THIS_DIR.parent / "occupations" / "occupations.json"
DROPPED_LOG = _THIS_DIR / "dropped.jsonl"
PROGRESS_LOG = _THIS_DIR / ".enrich_progress.log"
STATE_FILE = _THIS_DIR / ".enrich_state.json"

# Education levels excluded from the candidate occupation pool. The
# canonical definition lives in `backend/ontology/oes.py` so it has one
# home shared between Pass 3 (here) and the OES loader. Refined for
# CTE-relevance: HS-diploma roles ARE CTE-trainable via certificates
# (welding, CDL, CNA), and Master's roles are legitimate for academic-
# employer faculty hiring (community colleges feed those via transfer
# programs). The exclusions are roles where CTE has no plausible
# training pathway:
#   - "No formal educational credential" — no credentialing happens
#   - "Some college, no degree" — non-credentialing endpoint
#   - "Doctoral or professional degree" — out of CTE scope (MD, JD, PhD)
from ontology.oes import EXCLUDE_EDUCATION as _EXCLUDE_EDUCATION  # noqa: E402

# One employer per Gemini call. Gives the model the full prompt budget
# for one URL fetch + structured extraction; concurrency does the
# throughput. Batching multiple employers per call would amortize
# prompt tokens but complicates schema (per-employer arrays) and gives
# up the natural per-employer error boundary.
_DEFAULT_CONCURRENCY = 10
_INCREMENTAL_WRITE_EVERY = 20

# One retry on transient 5xx/429 with this back-off; then mark the
# employer's relevant fields absent and move on (next run retries).
_TRANSIENT_RETRY_SLEEP = 30.0

# Description floor in characters. ~60 words ≈ 350 chars. Validated
# post-parse, not via response_schema minLength (Gemini's schema
# support for minLength is uneven across model versions).
# Description bounds tuned for discovery-stage scanning. ~30-50 words is
# enough to capture core activity + scale + customer type without bloating
# the atlas card view. The 175-char floor still rejects vapid 12-word
# fallback descriptions ("A bakery operation.").
_DESCRIPTION_MIN_CHARS = 175
_DESCRIPTION_TARGET_WORDS = (30, 50)

# Occupations bounds tuned for signal density. 1 minimum honors employers
# whose CTE-relevant hiring profile is genuinely a single role (a
# specialty welding shop, a sole-electrician contractor, a hyper-narrow
# practice). Forcing a 2-floor would pad those records with marginal
# secondary roles that dilute signal. 5 maximum still forces the model
# to concentrate on the most representative roles for diversified
# employers.
_OCC_MIN = 1
_OCC_MAX = 5

# Phrases that signal "the model couldn't read the URL" leaking into
# fields. Same set as populate_description.py uses.
_LLM_FAILURE_PATTERNS = (
    "i am unable to",
    "i cannot",
    "i could not",
    "unable to access",
    "unable to provide",
    "cannot provide",
    "website content could not be",
    "website could not be browsed",
    "url could not be fetched",
    "url could not be accessed",
    "url could not be browsed",
    "no description can be",
    "no description could be",
    "i don't have access",
    "i do not have access",
    "page unreadable",
    "error fetching",
    "error in fetching",
    "could not be browsed",
    "the provided url could not",
    "failed to fetch",
)


def _is_failure_leak(text: str) -> bool:
    if not text:
        return True
    lower = text.strip().lower()
    return any(p in lower for p in _LLM_FAILURE_PATTERNS)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _progress(msg: str) -> None:
    line = f"[{_now_iso()}] {msg}"
    print(line, flush=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(line + "\n")


def _write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _append_dropped(entry: dict) -> None:
    with open(DROPPED_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google import genai
    return genai.Client(api_key=api_key)


# ── Tool selection ───────────────────────────────────────────────────────

def _pick_tools(types_module, search_only: bool) -> list:
    """Single-tool config per call.

    Multi-tool [url_context, google_search] tells the model to use either,
    but the model often invokes BOTH on success cases — pays a grounding
    fee for nothing. Single-tool per call eliminates that and pairs with
    explicit within-run escalation (url_context first; on failure, retry
    with search-only).
    """
    if search_only:
        return [types_module.Tool(google_search=types_module.GoogleSearch())]
    return [types_module.Tool(url_context=types_module.UrlContext())]


# ── Sector definitions ───────────────────────────────────────────────────
# Sharpened with adjacent-sector disambiguation. Each definition leads
# with the core value-creation activity, then 2-3 anchor examples, then
# explicit "not this sector" boundaries against the most-confused
# neighbors. The boundaries embed the failure cases observed during
# pipeline development (Xerox, Caito, Saputo) so future iterations
# don't recur.

_SECTOR_DEFINITIONS_SHARPENED: dict[str, str] = {
    "Advanced Manufacturing": (
        "Core: producing physical products through industrial processes. "
        "Examples: Boeing, Medtronic, Pacific Steel Castings. "
        "NOT Global Trade — wholesale distributors who do not produce. "
        "NOT Agriculture (AWET) for food/beverage manufacturers in NAICS 311–312 "
        "(dairy, beverages, meat processing) — those go to AWET. AMAT covers "
        "non-food manufacturing (NAICS 31x non-food, 32x, 33x)."
    ),
    "Advanced Transportation and Logistics": (
        "Core: moving people, goods, or vehicles at scale; warehousing and "
        "freight forwarding. Examples: UPS, a metropolitan transit system, a "
        "freight carrier, a truck-fleet operator. "
        "NOT Advanced Manufacturing — a depot that refurbishes/maintains "
        "equipment is AMAT (industrial process), not ATL (movement). "
        "NOT Global Trade — ATL covers moving the goods; Global Trade covers "
        "intermediating the sale."
    ),
    "Agriculture, Water and Environmental Technologies": (
        "Core: growing, harvesting, or processing agricultural products; "
        "operating water and environmental systems; processing food and "
        "beverages from raw agricultural inputs. "
        "Examples: Foster Farms, Woolf Farming, a regional water district, "
        "Saputo Cheese, Land O'Lakes, Fetzer Vineyards (food/beverage "
        "processing under NAICS 311–312). "
        "NOT Advanced Manufacturing — food and beverage producers belong in "
        "AWET per the canonical PCAH NAICS-3115/3121 mapping. "
        "NOT Retail (RHT) — wholesale ag distributors and farms producing "
        "for downstream sale are AWET; storefront grocers selling direct to "
        "consumers are RHT."
    ),
    "Business and Entrepreneurship": (
        "Core: providing professional services that support other businesses' "
        "operations — consulting, marketing, accounting, advertising, business "
        "process support, B2B technology services. "
        "Examples: Deloitte, a marketing agency, a management consulting firm, "
        "an IT services firm serving SMBs, Xerox Business Solutions (B2B "
        "document/print services). "
        "NOT Global Trade — B&E delivers a service; Global Trade intermediates "
        "physical goods. A B2B services firm that sells software, hardware, "
        "and managed services is B&E (or ICT if their core is software/networks), "
        "not Global Trade. "
        "NOT ICT — B&E covers cross-functional business services; ICT is "
        "specifically tech/media production."
    ),
    "Education and Human Development": (
        "Core: teaching, training, social services for children and families. "
        "Examples: a K-12 school district, a community college, a child "
        "welfare agency, a vocational training program. "
        "NOT Health — clinical/healthcare services, even at academic medical "
        "centers and tribal health systems, belong in Health. A 'Tribal Health "
        "System' is Health, not EHD, even when run by a tribal entity. "
        "NOT Government services — a city government providing utilities and "
        "infrastructure goes to ECU; EHD covers educational and social-services "
        "providers specifically."
    ),
    "Energy, Construction and Utilities": (
        "Core: building, maintaining, or operating physical infrastructure, "
        "properties, or utility systems; trades work. "
        "Examples: Clark Brothers Construction, a utility company, a "
        "landscape contractor, a city government providing utilities and "
        "public works. "
        "NOT Advanced Manufacturing — a manufacturer of HVAC equipment is AMAT; "
        "a contractor who installs HVAC systems is ECU."
    ),
    "Global Trade": (
        "Core: intermediating between producers and buyers at scale — "
        "wholesale distribution, import/export — WITHOUT producing the goods "
        "themselves. "
        "Examples: Sysco (wholesale food distributor — does not produce food), "
        "Caito Fisheries (wholesale seafood dealer — does not catch the fish), "
        "an electronics import-export company. "
        "NOT Advanced Manufacturing — if the entity transforms inputs into "
        "physical products, it is AMAT (or AWET for food). Wholesale = no "
        "transformation. "
        "NOT B&E — Global Trade covers physical-goods distribution; "
        "professional services to businesses are B&E. "
        "NOT Health — a wholesale medical equipment distributor is Global "
        "Trade ONLY if it doesn't deliver care; medical equipment + care = Health."
    ),
    "Health": (
        "Core: delivering healthcare services to patients. "
        "Examples: a hospital, a medical clinic, a dental practice, a "
        "skilled nursing facility, a home health agency, a tribal health "
        "system, an in-home care provider. "
        "NOT Global Trade — a 'medical resources' or 'medical equipment' "
        "company that provides clinical care services is Health, even if "
        "the name suggests distribution. Read the description carefully: "
        "if the entity delivers care to patients, it is Health."
    ),
    "Information and Communication Technologies - Digital Media": (
        "Core: producing or operating software, digital services, "
        "telecommunications networks, or media content. "
        "Examples: Palo Alto Networks, a telecommunications provider, "
        "a software-as-a-service company, a regional cable/internet provider "
        "(e.g., Suddenlink, Optimum). "
        "NOT B&E — ICT covers tech/media production specifically; B&E covers "
        "broader business services."
    ),
    "Life Sciences - Biotechnology": (
        "Core: biological research, drug discovery, genomic/diagnostic "
        "investigation. Output is scientific knowledge, novel compounds, or "
        "research findings. "
        "Examples: Genentech, Amgen, Scripps Research."
    ),
    "Public Safety": (
        "Core: protecting public safety — law enforcement, emergency response, "
        "corrections, judicial operations, fire protection. "
        "Examples: a sheriff's department, a fire department, a district "
        "attorney's office, a coroner's office, a correctional facility, a "
        "private security firm with sworn officer functions."
    ),
    "Retail, Hospitality and Tourism": (
        "Core: selling directly to consumers, providing hospitality, "
        "operating recreational/entertainment venues. "
        "Examples: a grocery chain, a hotel, a restaurant, a theme park, a "
        "specialty retailer (S-S Organic Produce — a retail grocer in Chico — "
        "is RHT, not AWET, because it operates a storefront serving consumers)."
    ),
}


def _load_sector_definitions() -> dict[str, str]:
    """Return sector definitions. Sharpened version is the source of truth here;
    the original `classify_employers._SECTOR_DEFINITIONS` is preserved for
    backward compatibility with the audit script."""
    return dict(_SECTOR_DEFINITIONS_SHARPENED)


# ── Region context ───────────────────────────────────────────────────────

def _region_display(regions: list[str]) -> str:
    """Human-readable region context for prompts."""
    from ontology.regions import COE_REGION_DISPLAY
    if not regions:
        return "California"
    if len(regions) == 1:
        return f"{COE_REGION_DISPLAY.get(regions[0], regions[0])} region of California"
    names = [COE_REGION_DISPLAY.get(r, r) for r in regions]
    return f"multiple California regions ({', '.join(names)})"


# ── OES NAICS-bounded occupation pool (C13) ──────────────────────────────
#
# Pre-C13: Pass 3 selected SOCs from a region-wide CTE-pathway pool (~700
# SOCs unioned across the employer's regions, filtered by
# `_EXCLUDE_EDUCATION`). The pool was institutionally sourced as a list
# of California career-track occupations, but it was not industry-
# anchored — a water utility and a software company in the same region
# saw the same candidate set, leading to documented domain-signature
# failures (Otay Water without water/wastewater operators, Cisco
# without software developers).
#
# Post-C13: Pass 3 selects from the BLS OEWS National Industry-
# Occupation Matrix at the deepest NAICS resolution BLS publishes for
# the employer's industry (descent rule: NAICS-4 → NAICS-3 → NAICS-2),
# intersected with `_EXCLUDE_EDUCATION` to preserve the CCC-scope
# constraint. The institutional anchor for layer 1 is now the BLS
# industry-occupation matrix; the only LLM judgment is which of the
# institutionally-published, industry-relevant SOCs apply to this
# specific employer.

_OES_MAX_CANDIDATES = 200


def _education_filter() -> set[str]:
    """SOCs whose education_level is NOT in `_EXCLUDE_EDUCATION`. Loaded
    once per process and cached as a function attribute. Returns the
    set of CTE-eligible SOC codes used to filter the OES industry pool.
    """
    if not hasattr(_education_filter, "_cache"):
        with open(OCCUPATIONS_PATH) as f:
            occs = json.load(f)
        _education_filter._cache = {
            o["soc_code"] for o in occs
            if o.get("education_level") not in _EXCLUDE_EDUCATION
        }
    return _education_filter._cache


def _employer_occ_list(employer: dict) -> list[dict]:
    """OES industry-occupation pool for one employer. Returns dicts
    shaped for `_build_occupations_prompt` (`{soc_code, title, ...}`).

    Returns [] if the employer has no `naics4` (the C13 historical
    backfill couldn't classify) or if BLS doesn't publish data at any
    NAICS resolution for that industry (e.g., NAICS 92 / Public
    Administration is genuinely uncovered by the OEWS national matrix).
    Empty pool ⇒ Pass 3 produces empty occupations ⇒ no HIRES_FOR
    edges ⇒ employer doesn't appear in partnerships landscape (C12-
    aligned exclusion mechanism, no special-case code).

    Sort: descending by `pct_total` so the most-characteristic
    occupations for the industry appear first in the prompt's
    constrained list. Capped at `_OES_MAX_CANDIDATES` rows; this
    mainly affects NAICS-2 fallbacks where the industry pool can
    exceed 200 entries.
    """
    from ontology.oes import oes_socs_for_naics4
    naics4 = employer.get("naics4")
    if not naics4:
        return []
    rows = oes_socs_for_naics4(naics4)
    if not rows:
        return []
    edu_socs = _education_filter()
    filtered = [
        {
            "soc_code": r["soc"],
            "title": r["title"],
            "pct_total": r["pct_total"],
        }
        for r in rows
        if r["soc"] in edu_socs
    ]
    filtered.sort(key=lambda r: -(r["pct_total"] or 0))
    return filtered[:_OES_MAX_CANDIDATES]


# ── PASS 1: Identity probe ────────────────────────────────────────────────
#
# Schema-enforced structured output is incompatible with `tools=[url_context]`
# (Gemini API: "Tool use with a response mime type: 'application/json' is
# unsupported"). We get the URL fetch via url_context and the structure via
# a JSON-only prompt + post-parse validation. The validator below covers what
# response_schema would have caught (field types, enum membership, length floor).


def _build_probe_prompt(employer: dict, search_only: bool = False) -> str:
    region_display = _region_display(employer.get("regions", []))
    if search_only:
        tool_block = (
            "Only the google_search tool is available. The url_context "
            "fetcher already failed for this URL on a prior attempt — DO NOT "
            "report 'page unreadable' as a justification for match=false. "
            "Instead: use google_search to research this employer "
            "thoroughly. Search by employer name + region, by employer name "
            "+ industry, and by the URL itself. Google's index has cached "
            "content from sites that direct fetching cannot retrieve. Use "
            "the search results to determine whether the URL belongs to "
            "this employer.\n\n"
        )
    else:
        tool_block = (
            "Two tools are available and you should use them as a fallback chain:\n"
            "1. url_context — fetch the URL directly. Try this first.\n"
            "2. google_search — query Google's index for the employer name and "
            "URL. Use this when url_context fails (404, JS-only page, anti-bot "
            "block, redirect chain) OR returns empty/thin content. Google's index "
            "often has cached rendered content for sites that fetcher tools can't "
            "reach. Only return 'page unreadable' if BOTH tools fail to produce "
            "any useful content about this employer.\n\n"
        )
    return (
        "You are verifying whether a candidate URL represents a specific "
        "employer. Read the page at the URL below and decide whether it "
        "represents the employer described.\n\n"
        + tool_block +
        f"URL: {employer['website']}\n\n"
        "EMPLOYER:\n"
        f"- Name: {employer['name']}\n"
        f"- Sector: {employer.get('sector', 'unknown')}\n"
        f"- Region: {region_display}\n\n"
        "MATCH criteria (any one is sufficient — a page only needs to "
        "represent the employer in some defensible institutional sense, not "
        "exactly mirror the EDD-listed name):\n"
        "- The corporate root of a national or multi-state brand whose name "
        "matches the employer name. Geographic mention is not required for "
        "well-known brands.\n"
        "  • Example: employer 'Saputo Cheese USA' + URL saputocheeseusa.com → MATCH\n"
        "  • Example: employer 'Anheuser-Busch Sales Beach' + URL ab-sales.com (corporate sales arm) → MATCH\n"
        "- A parent organization, holding company, or umbrella network that "
        "includes this employer as a facility, subsidiary, or branch.\n"
        "  • Example: employer 'Desert Regional Medical Center' + URL desertcarenetwork.com (parent network listing this hospital) → MATCH\n"
        "- An identifiable branded instance of the employer on a chain or "
        "system website — a property page for a hotel on the chain's site, a "
        "school page on a district's site, a clinic page on a system's site. "
        "Deep paths are OK as long as the page is clearly about this specific "
        "instance.\n"
        "  • Example: employer 'Anaheim Marriott Suites' + URL marriott.com/en-us/hotels/.../anaheim-marriott-suites/overview/ → MATCH\n"
        "  • Example: employer 'Coachella City Police Department' + URL coachella.org/departments/police-department → MATCH\n"
        "- A direct page that names this employer and operates in California.\n"
        "  • Example: employer 'Freund Baking' + URL freundbaking.com (the local bakery's own site) → MATCH\n\n"
        "MISMATCH criteria — return match=false ONLY when one of these is "
        "clearly true:\n"
        "- The page is for a different organization with a similar name in a "
        "different state or industry (e.g., a same-name firm in another state, "
        "or a totally unrelated business that happens to share a word).\n"
        "- The page is parked, expired, returns an error, or has no business "
        "identity at all.\n"
        "- The page is generic content (a directory listing, a category page, "
        "a 404) that contains no specific organizational identity.\n\n"
        "Calibration: a wrong URL is worse than dropping a legitimate "
        "employer, but a legitimate branded instance, parent organization, or "
        "in-California local employer should still MATCH. Do not require "
        "verbatim name equality — semantic match is enough. When the page "
        "credibly represents this employer or its parent in any of the senses "
        "above, return match=true.\n\n"
        "Output a single JSON object and nothing else (no prose, no markdown "
        "fences):\n"
        "{\"match\": true|false, \"evidence\": \"<short verbatim quote from the page>\"}\n\n"
        "The evidence field must contain a short verbatim quote from the page "
        "that grounds your decision — for match=true, a quote that demonstrates "
        "the represent-this-employer relationship; for match=false, a quote "
        "showing the mismatch (or 'page unreadable: <reason>')."
    )


async def _probe_async(client, types, employer: dict, label: str) -> dict | None:
    """Run identity probe with within-run escalation.

    Pass 1 — multi-tool: model picks url_context or google_search based on
    which yields content. Most cases resolve here.

    Pass 2 — search-only escalation: when pass 1 returns fetch_fail, force
    a google_search-only retry with an explicit "do not report page
    unreadable; use search" instruction. Collapses the multi-tool's "model
    didn't try search hard enough" failure mode into a deterministic
    retry. Only true API failures (None) still defer across runs.
    """
    result = await _probe_call(client, types, employer, label, search_only=False)
    if result is None:
        return None  # API/parse failure — defer
    if not result["fetch_fail"]:
        return result  # match or genuine mismatch — pass 1 was conclusive
    _progress(f"    {label}: probe escalating to search-only")
    result2 = await _probe_call(client, types, employer, f"{label}/search", search_only=True)
    if result2 is None:
        return result  # escalation API-failed; report pass-1 fetch_fail outcome
    if result2["fetch_fail"]:
        return result2  # still couldn't resolve via search either
    return result2  # search resolved it — match or mismatch decision


async def _probe_call(client, types, employer: dict, label: str, search_only: bool) -> dict | None:
    """Single Gemini probe invocation. Returns parsed result or None on API/parse failure.

    Single-tool config per call — url_context only or google_search only — to
    avoid the multi-tool case where the model invokes BOTH on success cases
    (paying a grounding fee unnecessarily). Within-run escalation handles
    the fallback chain.
    """
    prompt = _build_probe_prompt(employer, search_only=search_only)
    tools = _pick_tools(types, search_only=search_only)
    config = types.GenerateContentConfig(
        tools=tools,
        temperature=0.0,
    )

    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                _progress(f"    {label}: probe transient, retry in {int(_TRANSIENT_RETRY_SLEEP)}s — {e}")
                await asyncio.sleep(_TRANSIENT_RETRY_SLEEP)
                continue
            _progress(f"    {label}: probe FAIL — {type(e).__name__}: {e}")
            return None

    if response is None or not response.text:
        _progress(f"    {label}: probe FAIL — empty response")
        return None

    # Tool-mode disallows response_mime_type=json, so the model may emit
    # the JSON wrapped in markdown fences or with surrounding prose.
    # Extract the first {...} block.
    text = response.text.strip()
    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        _progress(f"    {label}: probe FAIL — no JSON object in response")
        return None
    try:
        parsed = json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        _progress(f"    {label}: probe FAIL — JSON parse: {e}")
        return None

    match = parsed.get("match")
    evidence = (parsed.get("evidence") or "").strip()
    if not isinstance(match, bool):
        _progress(f"    {label}: probe FAIL — match field missing/invalid")
        return None

    # match=true with empty or failure-leak evidence → treat as fetch failure.
    # The model claimed match without producing evidence; not trustworthy.
    if match and (not evidence or _is_failure_leak(evidence)):
        _progress(f"    {label}: probe FAIL — match=true but no evidence")
        return None

    # Distinguish three cases the orchestrator must handle differently:
    #   1. API/parse failure (return None above) — transient, defer.
    #   2. Page unreadable (model browsed, content failed) — could be a
    #      bad URL (404, dead domain) or a tool-side issue. Empirically
    #      most commonly bad URL. Trigger retry-search like a mismatch,
    #      with a safety net: if search confirms no alternative, defer
    #      (don't drop a possibly-good URL on transient tool issues).
    #   3. Genuine mismatch (model read the page, says it's the wrong
    #      org) — retry-search; drop if no alternative.
    fetch_fail = (not match) and _is_failure_leak(evidence)

    snippet = evidence.replace("\n", " ")[:160]
    if fetch_fail:
        _progress(f"    {label}: probe FETCH-FAIL: {snippet!r}")
    else:
        _progress(f"    {label}: probe match={match} evidence={snippet!r}")

    return {"match": match, "evidence": evidence, "fetch_fail": fetch_fail}


# ── Retry: re-search via Gemini grounding ─────────────────────────────────

async def _research_url_async(
    client,
    types,
    employer: dict,
    prior_url: str,
    label: str,
) -> tuple[str, str | None]:
    """Re-search for the employer's correct URL given that prior_url was wrong.

    Returns a (action, url) tuple:
      ("url", new_url) — search proposes a different URL; orchestrator should re-probe
      ("remove", None) — search explicitly recommends REMOVE; strong drop signal
      ("none", None)   — search couldn't help (api failure, same URL, malformed reply)
    """
    region_display = _region_display(employer.get("regions", []))
    prompt = (
        f"Search the web for the official website of this employer in the "
        f"{region_display}. The URL '{prior_url}' could not be verified as "
        f"this employer's site — either the page represents a different "
        f"organization, or the URL is unreachable. Investigate.\n\n"
        f"EMPLOYER:\n"
        f"- Name: {employer['name']}\n"
        f"- Sector: {employer.get('sector', 'unknown')}\n"
        f"- Region: {region_display}\n\n"
        "Decide one of three outcomes:\n"
        "1. A DIFFERENT URL is the correct site for this employer. Return it. "
        "It must be the ROOT domain or a dedicated sub-site with its own "
        "content (not a deep facility-finder path).\n"
        "2. The original URL '" + prior_url + "' actually IS the right site "
        "for this employer (you can verify the employer is associated with "
        "this URL via search results, even if you couldn't fetch the page "
        "yourself). Return SAME.\n"
        "3. This employer has no real official web presence under any URL "
        "(or it is a sub-department, defunct entity, or other non-viable "
        "organization). Return REMOVE.\n\n"
        "Calibration: a wrong URL is worse than dropping a legitimate "
        "employer, but if search results show the original URL belongs to "
        "this employer, prefer SAME over REMOVE — the page may simply be "
        "JS-rendered or anti-bot blocked.\n\n"
        "Return JSON: {\"action\": \"url\"|\"same\"|\"remove\", \"url\": \"https://...\" or null}\n"
        "When action is 'same' or 'remove', url should be null.\n"
        "No markdown fences."
    )
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.0,
    )

    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                _progress(f"    {label}: research transient, retry in {int(_TRANSIENT_RETRY_SLEEP)}s — {e}")
                await asyncio.sleep(_TRANSIENT_RETRY_SLEEP)
                continue
            _progress(f"    {label}: research FAIL — {type(e).__name__}: {e}")
            return ("none", None)

    if response is None or not response.text:
        return ("none", None)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0] if "\n" in text else text[:-3]
    if text.startswith("json"):
        text = text[4:].strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return ("none", None)

    action = (parsed.get("action") or "").strip().lower()
    raw = (parsed.get("url") or "").strip()

    if action == "same":
        _progress(f"    {label}: research → SAME (original URL is correct)")
        return ("same", None)
    if action == "remove":
        _progress(f"    {label}: research → REMOVE")
        return ("remove", None)
    if action == "url" and raw and raw.startswith("http"):
        if raw.rstrip("/") == prior_url.rstrip("/"):
            # Model said "url" but echoed the prior URL — treat as SAME.
            _progress(f"    {label}: research → echoed prior URL, treating as SAME")
            return ("same", None)
        _progress(f"    {label}: research → new URL: {raw}")
        return ("url", raw)

    # Malformed response or ambiguous action — defer.
    _progress(f"    {label}: research → unparseable (action={action!r}, url={raw!r})")
    return ("none", None)


# ── PASS 2: Description ──────────────────────────────────────────────────
# Single-job: produce a 60–120 word description grounded in page content.
# Two-step tool escalation (url_context first, search-only fallback).


def _build_describe_prompt(
    employer: dict,
    search_only: bool = False,
) -> str:
    region_display = _region_display(employer.get("regions", []))
    if search_only:
        tool_block = (
            "Only the google_search tool is available. The url_context "
            "fetcher already failed for this URL on a prior attempt. Use "
            "google_search to research this employer thoroughly: search by "
            "employer name + region, by employer name + industry, and by the "
            "URL itself. Synthesize across multiple snippets. Search results "
            "count as real evidence; do NOT fabricate from priors.\n\n"
        )
    else:
        tool_block = (
            "Use the url_context tool to fetch the URL below. If the page "
            "renders enough content for you to produce a grounded "
            "description, do so. If url_context returns empty/thin content, "
            "respond with an empty description and we will retry via search.\n\n"
        )
    lo, hi = _DESCRIPTION_TARGET_WORDS
    return (
        "You are writing one structured-data field for an employer in a "
        "California community college workforce-development partnership "
        "database: the description.\n\n"
        + tool_block +
        f"URL: {employer['website']}\n\n"
        "EMPLOYER CONTEXT:\n"
        f"- Name: {employer['name']}\n"
        f"- Sector hint (from EDD/NAICS): {employer.get('sector', 'unknown')}\n"
        f"- Region: {region_display}\n\n"
        "TASK:\n"
        f"Write ONE paragraph, {lo}–{hi} words, describing what this "
        "organization does, who it serves, scale of operations, and key "
        "business activities. Ground every claim in the content you "
        "retrieved. Do not invent facts. The description is the canonical "
        "text shown in the atlas; it should be specific and informative, "
        "not generic.\n\n"
        "═══ CRITICAL: OUTPUT FORMAT ═══\n"
        "Your response MUST be a single JSON object — nothing else. No "
        "prose. No markdown fences. No narrative. Even if you used "
        "google_search and have rich research findings, do not narrate "
        "them — only emit the JSON with the description as the value.\n\n"
        "Begin your response with `{` and end with `}`.\n\n"
        "Example correct response:\n"
        "{\"description\": \"Land O'Lakes is a farmer-owned cooperative \"\n"
        " \"that produces dairy products including butter, cheese, and \"\n"
        " \"plant-based alternatives, serving consumers across the U.S.\"}\n\n"
        "If you cannot retrieve any usable content, return:\n"
        "{\"description\": \"\"}\n\n"
        "Now respond — JSON only:"
    )


# ── PASS 3: Occupations ──────────────────────────────────────────────────
# Single-job: pick 3–8 SOC codes from the constrained regional list. The
# prompt directs the model toward careers/jobs/team pages rather than
# About/Home content — different attentional focus from the description
# pass on the same substrate.


def _build_occupations_prompt(
    employer: dict,
    occ_list: list[dict],
    description: str,
    search_only: bool = False,
) -> str:
    region_display = _region_display(employer.get("regions", []))
    occ_lines = "\n".join(f"- {o['soc_code']}: {o['title']}" for o in occ_list)
    if search_only:
        tool_block = (
            "Only google_search is available. The url_context fetcher "
            "already failed. Use google_search aggressively:\n"
            f"  - Search '{employer['name']} careers'\n"
            f"  - Search '{employer['name']} jobs'\n"
            f"  - Search '{employer['name']} open positions'\n"
            f"  - Search '{employer['name']} team' or 'leadership'\n"
            "Synthesize role/title information from the snippets. Search "
            "results count as real evidence; do NOT fabricate.\n\n"
        )
    else:
        tool_block = (
            "Use url_context to fetch the URL below, but do NOT stop there. "
            "Most home pages don't list roles. To pick accurate occupations, "
            "you need to know what this employer hires for — and that lives "
            "on careers/jobs/team pages, not the home page.\n"
            f"After fetching the home page, search the careers/jobs section "
            "of this employer's site if it exists. If url_context returns "
            "empty or thin content, respond with empty occupations and we "
            "will retry via search.\n\n"
        )
    return (
        "You are picking SOC codes representing CTE-pathway roles this "
        "employer hires for in California. These codes drive partnership "
        "matching: the college's CTE programs train for them, and we need "
        "to know which apply to this employer.\n\n"
        + tool_block +
        f"URL: {employer['website']}\n\n"
        "EMPLOYER CONTEXT:\n"
        f"- Name: {employer['name']}\n"
        f"- Sector hint (from EDD/NAICS): {employer.get('sector', 'unknown')}\n"
        f"- Region: {region_display}\n"
        f"- Description (just generated, for context): {description}\n\n"
        f"TASK: select {_OCC_MIN}–{_OCC_MAX} SOC codes from the "
        "constrained list below.\n\n"
        "THE CONSTRAINED LIST IS THE UNIVERSE.\n"
        "You MUST select codes from the list — codes outside it will be "
        "rejected. Every code in the list represents a role California "
        "community college CTE programs train for; your job is to "
        "identify which apply to this employer. Do NOT search for or "
        "reference roles outside this list, even if they are this "
        "employer's most numerous workforce category.\n\n"
        "Apply ALL of these criteria:\n\n"
        "  (1) PLAUSIBLE FOR THIS EMPLOYER — pick roles this employer "
        "would have employees in. For diversified employers (a large "
        "retailer, a multi-line manufacturer, a school district), this "
        "means focusing on the CTE-pathway slices of their workforce — "
        "not their dominant retail/admin roles which may not be in the "
        "list at all. Examples:\n"
        "    - Big-box retailer (e.g., Home Depot): First-Line Retail "
        "Supervisors, HVAC mechanics (installation services), "
        "Maintenance/Repair Workers, Construction Managers — NOT cashiers "
        "(not in CTE pool).\n"
        "    - Hospital: RN, LPN, Medical Assistants, Health Services "
        "Manager.\n"
        "    - Cement/Concrete manufacturer: Truck Drivers, Excavating "
        "Operators, Industrial Machinery Mechanics, Plant Operators.\n"
        "    - School district: K-12 Teachers (excluded if Master's-only "
        "and not in pool), Bus Drivers, Janitorial Supervisors, Office "
        "Administrators.\n\n"
        "  (2) ON ITS OWN PAYROLL — exclude services performed by "
        "external agencies. A hospital does not employ police officers; a "
        "hotel does not employ firefighters; a school district does not "
        "employ road construction workers.\n\n"
        "  (3) OPERATIONAL OVER ADMIN — prefer roles tied to the "
        "employer's distinctive activities over generic business-support "
        "roles. HR Specialists (13-1071), Accountants (13-2011), General "
        "and Operations Managers (11-1021), Customer Service Reps, IT "
        "Support: these are CTE-relevant in principle but they "
        "characterize 'any business at scale' rather than this specific "
        "employer. Pick them ONLY if no operational alternative exists "
        "for this employer's CTE-pathway hiring profile.\n\n"
        "  (4) ALWAYS PICK AT LEAST 1 — every legitimate employer has at "
        "least one CTE-pathway role in their hiring profile. If your "
        "first pass yields zero, you are being too restrictive — look "
        "harder at the constrained list. Supervisor-track codes "
        "(First-Line Supervisors of *) and equipment/maintenance codes "
        "are nearly always applicable for any 100+ employee employer. "
        "Genuinely-narrow employers (a specialty welding shop, a "
        "single-doctor practice) honestly have 1–2 codes; diversified "
        "employers honestly have 3–5. Match the count to the employer.\n\n"
        f"CONSTRAINED OCCUPATION LIST ({len(occ_list)} entries — codes "
        "outside this list will be rejected):\n"
        f"{occ_lines}\n\n"
        "═══ CRITICAL: OUTPUT FORMAT ═══\n"
        "Your response MUST be a single JSON object — nothing else. No "
        "prose. No markdown fences. No explanatory narrative. Even if "
        "you used google_search and have rich research findings, do not "
        "narrate them — only emit the JSON.\n\n"
        "Begin your response with `{` and end with `}`.\n\n"
        "Example correct response:\n"
        "{\"occupations\": [\"41-1011\", \"49-9021\", \"49-9071\"]}\n\n"
        "Example INCORRECT response (prose narrative — will be rejected):\n"
        "I researched this employer and found that they hire for various "
        "roles including retail supervisors and HVAC technicians. The "
        "relevant SOC codes are 41-1011, 49-9021...\n\n"
        "If after looking carefully you cannot find any plausible "
        "matches in the constrained list, return:\n"
        "{\"occupations\": []}\n"
        "But this should be rare — almost all real employers have at "
        "least one matching code.\n\n"
        "Now respond — JSON only:"
    )


# ── PASS 4: Classification ──────────────────────────────────────────────
# Single-job: read the description, return one of 12 SWP sectors. NO
# tools — description is the substrate. Without tools we can use
# response_schema for strict enum enforcement. Output includes a
# "sector_evidence" reasoning step before the final answer to force
# deliberation.


def _build_classify_prompt(
    employer: dict,
    description: str,
    sectors: dict[str, str],
) -> str:
    sector_lines = "\n".join(f"- {s}: {desc}" for s, desc in sectors.items())
    return (
        "You are classifying an employer into exactly ONE Strong Workforce "
        "Program sector. The description below is the canonical statement "
        "of what this employer does — derived from their own website. Read "
        "it carefully and identify the single sector whose identity "
        "principle best matches the core value-creation activity.\n\n"
        f"EMPLOYER NAME: {employer['name']}\n\n"
        f"DESCRIPTION:\n{description}\n\n"
        "SECTOR DEFINITIONS (each lists core activity, examples, and "
        "explicit boundaries against adjacent sectors — pay attention to "
        "the 'NOT this sector' clauses):\n"
        f"{sector_lines}\n\n"
        "REASONING — before giving your final answer:\n"
        "1. Identify the core value-creation activity in 1 sentence (what "
        "does this organization fundamentally do to create value for "
        "customers?).\n"
        "2. Identify the 1-2 sectors that could plausibly fit, including "
        "the most-confused adjacent sector (e.g., AWET vs AMAT for food "
        "manufacturers; B&E vs Global Trade vs ICT for B2B tech services; "
        "Health vs Global Trade for medical companies; RHT vs AWET for "
        "retail food).\n"
        "3. Apply the 'NOT this sector' clauses to eliminate candidates.\n"
        "4. Pick the single sector that best matches.\n\n"
        "Return JSON only (response schema enforced):\n"
        "{\"core_activity\": \"...\", "
        "\"candidates_considered\": [\"...\"], "
        "\"swp_sector\": \"<one of the sector names>\"}"
    )


# ── Generic Gemini call helper ───────────────────────────────────────────
# Shared transport for Describe and Occupations passes. Classify uses
# response_schema and has its own helper since the API surface differs.


async def _gemini_text_call(
    client,
    types,
    prompt: str,
    label: str,
    search_only: bool,
    pass_name: str,
) -> dict | None:
    """Run a tool-using Gemini call and parse the first {...} block. Returns
    the parsed dict or None on transient/parse failure. Single-tool config
    (no multi-tool) — caller decides whether url_context or search."""
    tools = _pick_tools(types, search_only=search_only)
    config = types.GenerateContentConfig(tools=tools, temperature=0.0)
    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                _progress(f"    {label}: {pass_name} transient, retry in {int(_TRANSIENT_RETRY_SLEEP)}s — {e}")
                await asyncio.sleep(_TRANSIENT_RETRY_SLEEP)
                continue
            _progress(f"    {label}: {pass_name} FAIL — {type(e).__name__}: {e}")
            return None
    if response is None or not response.text:
        return None
    text = response.text.strip()
    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        _progress(f"    {label}: {pass_name} FAIL — no JSON object in response")
        return None
    try:
        return json.loads(json_match.group(0))
    except json.JSONDecodeError as e:
        _progress(f"    {label}: {pass_name} FAIL — JSON parse: {e}")
        return None


# ── Describe: orchestrator + single-call + validator ────────────────────


def _validate_description(parsed: dict | None) -> str | None:
    if parsed is None:
        return None
    desc = (parsed.get("description") or "").strip()
    if not desc or len(desc) < _DESCRIPTION_MIN_CHARS or _is_failure_leak(desc):
        return None
    return desc


async def _describe_call(client, types, employer, label, search_only) -> str | None:
    prompt = _build_describe_prompt(employer, search_only=search_only)
    parsed = await _gemini_text_call(client, types, prompt, label, search_only, "describe")
    return _validate_description(parsed)


async def _describe_async(client, types, employer, label) -> str | None:
    """Two-step: url_context first; on failure, retry search-only."""
    desc = await _describe_call(client, types, employer, label, search_only=False)
    if desc is not None:
        return desc
    _progress(f"    {label}: describe escalating to search-only")
    return await _describe_call(client, types, employer, f"{label}/search", search_only=True)


# ── Occupations: orchestrator + single-call + validator ─────────────────


def _validate_occupations(parsed: dict | None, valid_socs: set[str]) -> list[str] | None:
    if parsed is None:
        return None
    occs_raw = parsed.get("occupations") or []
    if not isinstance(occs_raw, list):
        return None
    cleaned = [s for s in occs_raw if isinstance(s, str) and s in valid_socs]
    seen: set[str] = set()
    uniq = [c for c in cleaned if not (c in seen or seen.add(c))]
    if _OCC_MIN <= len(uniq) <= _OCC_MAX:
        return uniq
    if len(uniq) > _OCC_MAX:
        return uniq[:_OCC_MAX]
    return None


async def _occupations_call(client, types, employer, occ_list, description, label, search_only) -> list[str] | None:
    prompt = _build_occupations_prompt(employer, occ_list, description, search_only=search_only)
    parsed = await _gemini_text_call(client, types, prompt, label, search_only, "occupations")
    return _validate_occupations(parsed, {o["soc_code"] for o in occ_list})


async def _occupations_async(client, types, employer, occ_list, description, label) -> list[str] | None:
    occs = await _occupations_call(client, types, employer, occ_list, description, label, search_only=False)
    if occs is not None:
        return occs
    _progress(f"    {label}: occupations escalating to search-only")
    return await _occupations_call(client, types, employer, occ_list, description, f"{label}/search", search_only=True)


# ── Classify: single-call (no tools, response_schema enum-enforced) ─────
#
# The classifier reads the description (already produced by Describe) and
# returns one of 12 sectors. With NO tools attached, response_schema is
# allowed — strict enum enforcement on the sector field. The reasoning
# fields ("core_activity", "candidates_considered") force the model to
# deliberate before answering, which empirically reduces adjacent-sector
# confusion (Xerox: B&E vs Global Trade; Caito: Global Trade vs AMAT).


def _classify_schema(sectors: list[str]) -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "core_activity": {"type": "STRING"},
            "candidates_considered": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "swp_sector": {"type": "STRING", "enum": sectors},
        },
        "required": ["core_activity", "swp_sector"],
    }


async def _classify_async(client, types, employer, description, sectors, label) -> tuple[str | None, dict | None]:
    """Single call. Returns (sector, reasoning_dict) or (None, None) on failure.

    No tools → response_schema is allowed. Reasoning fields force deliberation.
    """
    if not description:
        return None, None
    prompt = _build_classify_prompt(employer, description, sectors)
    sector_keys = list(sectors.keys())
    schema = _classify_schema(sector_keys)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    )
    response = None
    for attempt in (1, 2):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            err = str(e).lower()
            is_transient = any(tok in err for tok in ("503", "429", "rate", "unavailable"))
            if is_transient and attempt == 1:
                _progress(f"    {label}: classify transient, retry in {int(_TRANSIENT_RETRY_SLEEP)}s — {e}")
                await asyncio.sleep(_TRANSIENT_RETRY_SLEEP)
                continue
            _progress(f"    {label}: classify FAIL — {type(e).__name__}: {e}")
            return None, None
    if response is None or not response.text:
        return None, None
    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError as e:
        _progress(f"    {label}: classify FAIL — JSON parse: {e}")
        return None, None
    sector = (parsed.get("swp_sector") or "").strip()
    if sector not in sectors:
        return None, None
    reasoning = {
        "core_activity": parsed.get("core_activity"),
        "candidates_considered": parsed.get("candidates_considered"),
    }
    return sector, reasoning


# ── Enrichment orchestrator: Describe → Occupations → Classify ──────────


async def _enrich_async(
    client,
    types,
    employer: dict,
    occ_list: list[dict],
    sectors: dict[str, str],
    label: str,
) -> tuple[str | None, list[str] | None, str | None]:
    """Three sequential single-job passes. Returns (description, occupations,
    sector). Each field can be None independently — the caller decides what
    to write.

    Description and Occupations use two-step tool escalation (url_context
    first, search-only fallback). Classify uses no tools and is enum-
    enforced via response_schema.

    Sequential ordering — Classify needs the description as input, so it
    runs after Describe completes. Occupations and Describe could be
    parallelized (independent), but sequential keeps the progress log
    linear and the architecture simple. Wall-time cost: ~5–8s extra per
    employer; with concurrency=10 this is amortized across batches.
    """
    desc = await _describe_async(client, types, employer, label)
    occs = await _occupations_async(client, types, employer, occ_list, desc or "", label)
    if desc is None:
        # No description means classify has no substrate. Skip; next-run
        # retry of Describe will re-trigger the chain.
        return None, occs, None
    sect, _reasoning = await _classify_async(client, types, employer, desc, sectors, label)
    return desc, occs, sect


# ── Per-employer orchestration ───────────────────────────────────────────

async def _process_employer(
    client,
    types,
    employer: dict,
    occ_list: list[dict],
    sectors: dict[str, str],
    label: str,
    skip_probe: bool,
    skip_enrich: bool,
) -> dict:
    """Run probe (with retry) then enrich. Returns a result dict for accounting."""
    out = {
        "name": employer["name"],
        "probe_status": None,      # "verified" | "dropped_mismatch" | "fetch_failed" | "skipped"
        "drop_reason": None,
        "drop_prior_url": None,
        "drop_retry_url": None,
        "enrich_desc": None,
        "enrich_occs": None,
        "enrich_sector": None,
    }

    if skip_probe:
        out["probe_status"] = "skipped"
    elif employer.get("identity_verified") is True:
        # Already verified in a prior run — no need to re-probe.
        out["probe_status"] = "verified"
    else:
        result = await _probe_async(client, types, employer, label)
        if result is None:
            # API/parse failure — pure transient. Defer.
            out["probe_status"] = "fetch_failed"
            return out

        if result["match"]:
            out["probe_status"] = "verified"
        else:
            # Decision table — `init` is whether the initial probe said
            # mismatch (read the page, wrong org) or fetch-failed (couldn't
            # read the page). The orchestrator drops only on concrete
            # evidence; ambiguous fetch-fail combinations defer.
            #
            #   init       | research action | next probe outcome | result
            #   -----------+-----------------+--------------------+--------------------
            #   mismatch   | url             | match              | adopt new URL
            #   mismatch   | url             | fetch_fail         | drop_unfetchable
            #   mismatch   | url             | mismatch           | drop_mismatch
            #   mismatch   | url             | api_fail (None)    | defer
            #   mismatch   | remove          | —                  | drop_mismatch
            #   mismatch   | none            | —                  | drop_mismatch
            #   fetch_fail | url             | match              | adopt new URL
            #   fetch_fail | url             | fetch_fail         | defer  (could be transient)
            #   fetch_fail | url             | mismatch           | drop_mismatch
            #   fetch_fail | url             | api_fail (None)    | defer
            #   fetch_fail | remove          | —                  | drop_unfetchable
            #   fetch_fail | none            | —                  | defer
            prior_url = employer["website"]
            initial_fetch_fail = result["fetch_fail"]
            action, new_url = await _research_url_async(client, types, employer, prior_url, label)

            if action == "remove":
                if initial_fetch_fail:
                    out["probe_status"] = "dropped_unfetchable"
                    out["drop_reason"] = "fetch failed on prior URL; research recommends REMOVE"
                else:
                    out["probe_status"] = "dropped_mismatch"
                    out["drop_reason"] = "prior URL was a mismatch; research recommends REMOVE"
                out["drop_prior_url"] = prior_url
                return out

            if action == "same":
                # Search affirms the original URL is the correct one for
                # this employer, even though probe couldn't read it. Mark
                # as verified — we have second-source evidence the URL is
                # right; the page just won't render for the fetcher.
                # Enrichment will still attempt to read it (with the
                # google_search fallback in the prompt), so description
                # quality is not sacrificed.
                if initial_fetch_fail:
                    out["probe_status"] = "verified"
                else:
                    # Initial was a real mismatch but search says SAME.
                    # Conflicting signals — defer rather than guess.
                    out["probe_status"] = "fetch_failed"
                return out

            if action == "none":
                if initial_fetch_fail:
                    out["probe_status"] = "fetch_failed"
                else:
                    out["probe_status"] = "dropped_mismatch"
                    out["drop_reason"] = "probe mismatch; research returned no alternative"
                    out["drop_prior_url"] = prior_url
                return out

            # action == "url" → probe new URL.
            employer_retry = dict(employer)
            employer_retry["website"] = new_url
            result2 = await _probe_async(client, types, employer_retry, f"{label}/retry")

            if result2 is None:
                out["probe_status"] = "fetch_failed"
                return out

            if result2["match"]:
                employer["website"] = new_url
                out["probe_status"] = "verified"
                out["drop_retry_url"] = new_url  # signal: URL rotated
            elif result2["fetch_fail"]:
                if initial_fetch_fail:
                    # Both URLs unreadable — could be Gemini being flaky.
                    # Defer rather than drop a potentially-good employer.
                    out["probe_status"] = "fetch_failed"
                    return out
                else:
                    # Initial was real mismatch; research-suggested URL
                    # unreachable. We've established the original is wrong
                    # and the alternative can't be verified — drop.
                    out["probe_status"] = "dropped_unfetchable"
                    out["drop_reason"] = "prior URL was a mismatch; research-suggested URL unreadable"
                    out["drop_prior_url"] = prior_url
                    out["drop_retry_url"] = new_url
                    return out
            else:
                # Genuine mismatch on the new URL → drop.
                out["probe_status"] = "dropped_mismatch"
                out["drop_reason"] = "probe mismatch on both prior and research-suggested URL"
                out["drop_prior_url"] = prior_url
                out["drop_retry_url"] = new_url
                return out

    if skip_enrich:
        return out
    if out["probe_status"] != "verified":
        return out

    # Skip enrichment if all shadow fields already populated (idempotent).
    if (
        employer.get("_description")
        and employer.get("_occupations")
        and employer.get("_swp_sector")
    ):
        return out

    desc, occs, sector = await _enrich_async(
        client, types, employer, occ_list, sectors, label
    )
    out["enrich_desc"] = desc
    out["enrich_occs"] = occs
    out["enrich_sector"] = sector
    return out


# ── Run loop ─────────────────────────────────────────────────────────────

async def _run_all(
    client,
    types,
    targets: list[dict],
    employers_full: list[dict],
    sectors: dict[str, str],
    concurrency: int,
    dry_run: bool,
    skip_probe: bool,
    skip_enrich: bool,
    state: dict,
) -> dict:
    sem = asyncio.Semaphore(concurrency)
    write_lock = asyncio.Lock()
    n = len(targets)
    totals = {
        "done": 0,
        "verified": 0,
        "url_rotated": 0,
        "dropped_mismatch": 0,
        "dropped_unfetchable": 0,
        "probe_fetch_failed": 0,
        "enrich_desc_set": 0,
        "enrich_occs_set": 0,
        "enrich_sector_set": 0,
        "enrich_partial_failure": 0,
    }
    drop_set: set[str] = set()

    name_to_emp = {e["name"]: e for e in employers_full}

    async def process(idx: int, emp: dict) -> None:
        async with sem:
            label = f"emp {idx + 1}/{n} {emp['name'][:40]}"
            t0 = time.monotonic()
            occ_list = _employer_occ_list(emp)
            res = await _process_employer(
                client, types, emp, occ_list, sectors, label,
                skip_probe, skip_enrich,
            )
            elapsed = time.monotonic() - t0

            async with write_lock:
                # Apply probe outcome.
                live = name_to_emp[emp["name"]]
                if res["probe_status"] == "verified":
                    live["identity_verified"] = True
                    if res["drop_retry_url"]:
                        live["website"] = res["drop_retry_url"]
                        totals["url_rotated"] += 1
                    totals["verified"] += 1
                elif res["probe_status"] in ("dropped_mismatch", "dropped_unfetchable"):
                    drop_set.add(emp["name"])
                    _append_dropped({
                        "name": emp["name"],
                        "status": res["probe_status"],
                        "reason": res["drop_reason"],
                        "prior_url": res["drop_prior_url"],
                        "retry_url": res["drop_retry_url"],
                        "regions": emp.get("regions", []),
                        "sector": emp.get("sector"),
                        "dropped_at": _now_iso(),
                    })
                    totals[res["probe_status"]] += 1
                elif res["probe_status"] == "fetch_failed":
                    totals["probe_fetch_failed"] += 1
                # "skipped" is silent.

                # Apply enrichment outcomes (independent fields).
                if res["probe_status"] == "verified" and not skip_enrich:
                    fields_set = 0
                    if res["enrich_desc"] is not None:
                        live["_description"] = res["enrich_desc"]
                        totals["enrich_desc_set"] += 1
                        fields_set += 1
                    if res["enrich_occs"] is not None:
                        live["_occupations"] = res["enrich_occs"]
                        totals["enrich_occs_set"] += 1
                        fields_set += 1
                    if res["enrich_sector"] is not None:
                        live["_swp_sector"] = res["enrich_sector"]
                        totals["enrich_sector_set"] += 1
                        fields_set += 1
                    if 0 < fields_set < 3:
                        totals["enrich_partial_failure"] += 1

                totals["done"] += 1
                _progress(
                    f"  {label}: probe={res['probe_status']} "
                    f"desc={'✓' if res['enrich_desc'] else '·'} "
                    f"occs={'✓' if res['enrich_occs'] else '·'} "
                    f"sect={'✓' if res['enrich_sector'] else '·'} "
                    f"{elapsed:.1f}s ({totals['done']}/{n})"
                )

                state.update({
                    **{k: v for k, v in totals.items()},
                    "updated_at": _now_iso(),
                })
                _write_state(state)

                if not dry_run and totals["done"] % _INCREMENTAL_WRITE_EVERY == 0:
                    _write_employers(employers_full, drop_set)
                    _progress(f"  checkpoint: wrote employers.json after {totals['done']} done")

    await asyncio.gather(*[process(i, t) for i, t in enumerate(targets)])

    # Final write.
    if not dry_run:
        _write_employers(employers_full, drop_set)
        _progress(f"Final write: employers.json ({len(employers_full) - len(drop_set)} kept)")

    return totals


def _write_employers(employers_full: list[dict], drop_set: set[str]) -> None:
    kept = [e for e in employers_full if e["name"] not in drop_set]
    with open(EMPLOYERS_PATH, "w") as f:
        json.dump(kept, f, indent=2)


# ── Entry point ──────────────────────────────────────────────────────────

def enrich(
    region: str | None = None,
    limit: int | None = None,
    concurrency: int = _DEFAULT_CONCURRENCY,
    dry_run: bool = False,
    skip_probe: bool = False,
    skip_enrich: bool = False,
    force: bool = False,
) -> dict:
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    sectors = _load_sector_definitions()

    # Build target set.
    def _needs_work(e: dict) -> bool:
        if not e.get("website"):
            return False
        if force:
            return True
        # Already-promoted employers are done — their canonical fields are
        # populated and shadow fields were intentionally cleared by
        # cutover. Without this check, every default re-run after a
        # cutover would reprocess the entire promoted set (the
        # missing-shadow-fields check below incorrectly flags them as
        # incomplete). To re-enrich a promoted employer, use --force.
        if e.get("enrichment_promoted") is True:
            return False
        if not skip_probe and e.get("identity_verified") is not True:
            return True
        if not skip_enrich and not (
            e.get("_description") and e.get("_occupations") and e.get("_swp_sector")
        ):
            return True
        return False

    targets = [e for e in employers if _needs_work(e)]
    if region:
        targets = [e for e in targets if region in e.get("regions", [])]
    if limit:
        targets = targets[:limit]

    # Tag every targeted employer with `enrichment_attempted=True`. This is
    # the durable signal that distinguishes deferred employers (attempted
    # but not verified) from never-touched legacy employers. load.py uses
    # it to decide which records to load: attempted+verified → load with
    # new data; attempted-but-not-verified → exclude from Neo4j (don't ship
    # imperfect data); never-attempted → load with existing canonical data
    # (legacy baseline preserved until that region is enriched).
    for emp in targets:
        emp["enrichment_attempted"] = True

    PROGRESS_LOG.write_text("")
    state = {
        "started_at": _now_iso(),
        "total_employers": len(employers),
        "targets": len(targets),
        "concurrency": concurrency,
        "skip_probe": skip_probe,
        "skip_enrich": skip_enrich,
        "force": force,
        "region": region,
        "limit": limit,
    }
    _write_state(state)
    _progress(
        f"Started enrich: {len(targets)} targets, concurrency={concurrency}, "
        f"region={region}, limit={limit}, force={force}, "
        f"skip_probe={skip_probe}, skip_enrich={skip_enrich}"
    )

    if not targets:
        _progress("Nothing to do.")
        state["finished_at"] = _now_iso()
        _write_state(state)
        return state

    client = _get_gemini_client()
    from google.genai import types

    totals = asyncio.run(_run_all(
        client, types, targets, employers, sectors,
        concurrency, dry_run, skip_probe, skip_enrich, state,
    ))

    state.update(totals)
    state["finished_at"] = _now_iso()
    _write_state(state)
    _progress(f"Done: {totals}")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Two-pass website-grounded employer enrichment."
    )
    parser.add_argument("--region", type=str, default=None,
                        help="Limit to employers tagged with this COE region code")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N targets after filtering")
    parser.add_argument("--concurrency", type=int, default=_DEFAULT_CONCURRENCY)
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without writing employers.json (state and dropped.jsonl still written)")
    parser.add_argument("--skip-probe", action="store_true",
                        help="Run enrichment only; assumes identity already verified")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Run identity probe only; no enrichment")
    parser.add_argument("--force", action="store_true",
                        help="Re-process employers even if shadow fields are populated")
    args = parser.parse_args()

    # .env loading — pipeline/run.py does this for chained runs but
    # `python -m employers.enrich` bypasses that entry point.
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    state = enrich(
        region=args.region,
        limit=args.limit,
        concurrency=args.concurrency,
        dry_run=args.dry_run,
        skip_probe=args.skip_probe,
        skip_enrich=args.skip_enrich,
        force=args.force,
    )

    print("=" * 60)
    print("FINAL STATE")
    print("=" * 60)
    for k, v in state.items():
        print(f"  {k:30s}  {v}")
    if args.dry_run:
        print("(dry run — employers.json not modified)")


if __name__ == "__main__":
    main()
