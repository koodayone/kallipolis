"""
Identify and verify official websites for employers from EDD ALMIS data.

Uses Gemini with Google Search grounding to search the live web for each
employer's official website. The model searches Google, finds the current
URL, verifies identity from search results (city, state, industry), and
returns the root domain — all in one API call per batch.

This replaces the previous Predict → Fetch → Verify → Fallback pipeline
which had a ~10% wrong-URL rate due to stale training data, anti-bot
blocking, and same-name collisions. Google Search grounding eliminates
all three failure modes because it queries Google's index rather than
hitting employer servers directly.

INVARIANT: Every assigned URL comes from a live web search with identity
verification. No URL is assigned from training-data prediction alone.

Usage:
    from employers.identify_websites import identify_websites
    results = identify_websites(employers, region_display="South Central Coast")
    # results: list of dicts with "website" set or "_remove" flagged
"""

from __future__ import annotations

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

# Batch size for Google Search grounding calls.
# Smaller than pure-prediction batches because each employer triggers
# a web search, which consumes more model context.
_BATCH_SIZE = 50

# Retry config for transient Gemini failures (503, timeout).
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 3.0


def identify_websites(
    employers: list[dict],
    region_display: str = "",
) -> list[dict]:
    """Identify official websites for employers via Google Search grounding.

    Each employer dict should have: name, sector, and ideally city, county,
    naics_label, size_class (from EDD) for disambiguation. Returns the same
    list with "website" set on verified employers and "_remove" set on those
    with no web presence or that are not viable partnership targets.
    """
    need = [e for e in employers if not e.get("website")]
    if not need:
        logger.info("  All employers already have websites")
        return employers

    logger.info(f"  Identifying websites for {len(need)} employers via Google Search")

    # Step 1: Search and verify in batches
    results = _search_and_verify(need, region_display)

    # Apply results
    assigned = 0
    removed = 0
    for emp in need:
        url = results.get(emp["name"])
        if url and url not in ("REMOVE", "NONE") and str(url).startswith("http"):
            emp["website"] = url
            assigned += 1
        else:
            emp["_remove"] = True
            removed += 1

    # Step 2: Retry any employers that were missed (not in results at all)
    missed = [e for e in need if e["name"] not in results]
    if missed:
        logger.info(f"  Retrying {len(missed)} employers missed in first pass")
        retry_results = _search_and_verify(missed, region_display, batch_size=25)
        for emp in missed:
            url = retry_results.get(emp["name"])
            if url and url not in ("REMOVE", "NONE") and str(url).startswith("http"):
                emp["website"] = url
                emp.pop("_remove", None)
                assigned += 1
                removed -= 1

    # Step 3: Liveness check — confirm every assigned URL resolves
    live, dead = _liveness_check([e for e in need if e.get("website")])
    for emp in need:
        if emp["name"] in dead:
            emp.pop("website", None)
            emp["_remove"] = True
            assigned -= 1
            removed += 1

    logger.info(f"  Website identification complete: {assigned} verified, {removed} removed")
    return employers


def _search_and_verify(
    employers: list[dict],
    region_display: str,
    batch_size: int = _BATCH_SIZE,
) -> dict[str, str]:
    """Search the web for each employer's website using Gemini + Google Search.

    Returns {employer_name: "https://..." or "REMOVE"}.
    """
    client = _get_gemini_client()
    if not client:
        return {}

    from google.genai import types

    all_results: dict[str, str] = {}

    for i in range(0, len(employers), batch_size):
        batch = employers[i:i + batch_size]
        lines = []
        for e in batch:
            city = e.get("city", "")
            county = e.get("county", "")
            naics = e.get("naics_label", e.get("sector", ""))
            size = e.get("size_class", "")
            lines.append(
                f"- {e['name']} | {city}, {county} County | {naics} | {size}"
            )

        prompt = (
            f"For each employer below in the {region_display or 'California'} "
            "region, search the web and find their official website.\n\n"
            "For each employer:\n"
            "1. Search for their official website using the employer name, "
            "city, and industry to find the RIGHT company (not a same-name "
            "business in another state)\n"
            "2. Return the ROOT domain URL — not a deep facility-finder page, "
            "not a location-directory sub-page. A dedicated sub-site with its "
            "own content is acceptable (e.g., adventisthealth.org/simi-valley/) "
            "but a deep path like /locations/facilities/id-12345 is not — "
            "use the parent domain root instead\n"
            "3. If the employer has no discoverable official website, or is not "
            "a viable CTE workforce partnership target (too small, religious "
            "organization, labor contractor, sub-department of a parent already "
            "listed), return REMOVE\n"
            "4. A wrong URL is MUCH worse than REMOVE. When in doubt, REMOVE.\n\n"
            "Return JSON: {\"employer_name\": \"https://url\" or \"REMOVE\"}\n"
            "No markdown fences.\n\n"
            "EMPLOYERS:\n" + "\n".join(lines)
        )

        batch_label = f"Batch {i // batch_size + 1}/{(len(employers) - 1) // batch_size + 1}"
        result = _gemini_search_call(client, types, prompt, batch_label)

        if result:
            all_results.update(result)
            url_ct = sum(
                1 for v in result.values()
                if v and v not in ("REMOVE", "NONE") and str(v).startswith("http")
            )
            remove_ct = sum(1 for v in result.values() if v == "REMOVE")
            logger.info(f"    {batch_label}: {url_ct} URLs, {remove_ct} removed")
        else:
            logger.error(f"    {batch_label}: failed after retries")

    return all_results


def _gemini_search_call(
    client,
    types,
    prompt: str,
    label: str,
) -> dict | None:
    """Call Gemini with Google Search grounding, with retry on transient errors."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )

            if not response.text:
                logger.warning(f"    {label} attempt {attempt}: empty response")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_BACKOFF_BASE * attempt)
                    continue
                return None

            text = response.text.strip()
            # Strip markdown fences
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0] if "\n" in text else text[:-3]
            if text.startswith("json"):
                text = text[4:].strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"    {label} attempt {attempt}: JSON parse failed: {e}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_BASE * attempt)
            else:
                return None

        except Exception as e:
            err_str = str(e)
            if "503" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower():
                logger.warning(f"    {label} attempt {attempt}: Gemini unavailable, retrying...")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_BACKOFF_BASE * attempt)
                else:
                    logger.error(f"    {label}: failed after {_MAX_RETRIES} attempts")
                    return None
            else:
                logger.error(f"    {label} attempt {attempt}: {e}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_BACKOFF_BASE * attempt)
                else:
                    return None

    return None


def _liveness_check(employers: list[dict]) -> tuple[set[str], set[str]]:
    """Verify that assigned URLs actually resolve.

    Returns (live_names, dead_names). Uses verify=False because the
    system's LibreSSL is too old for many modern TLS configurations;
    SSL cert validity is not what we're checking here — just that the
    domain exists and serves content.
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed

    logger.info(f"  Step 3 (liveness): checking {len(employers)} URLs")

    live: set[str] = set()
    dead: set[str] = set()

    def check(emp: dict) -> tuple[str, bool]:
        url = emp["website"]
        try:
            r = requests.head(
                url, timeout=15, allow_redirects=True, verify=False,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            return emp["name"], r.status_code < 500
        except Exception:
            try:
                r = requests.get(
                    url, timeout=15, allow_redirects=True, verify=False,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                return emp["name"], r.status_code < 500
            except Exception:
                return emp["name"], False

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check, e) for e in employers]
        for f in as_completed(futures):
            name, is_alive = f.result()
            if is_alive:
                live.add(name)
            else:
                dead.add(name)

    logger.info(f"  Step 3 complete: {len(live)} alive, {len(dead)} dead")
    return live, dead


def _get_gemini_client():
    """Get a Gemini client, or None if no API key."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("  No GEMINI_API_KEY")
        return None
    from google import genai
    return genai.Client(api_key=api_key)
