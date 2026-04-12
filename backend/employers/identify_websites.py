"""
Identify and verify official websites for employers from EDD ALMIS data.

Three-step pipeline: Predict → Fetch → Verify, with WebSearch fallback.

Step 1 (PREDICT): Gemini predicts candidate URLs using full EDD context
    (name, city, county, NAICS, size) to disambiguate same-name collisions.
Step 2 (FETCH): Parallel HTTP GET to retrieve page content from candidates.
Step 3 (VERIFY): Gemini reads fetched page content and confirms the page
    belongs to the specific employer, catching wrong-company matches.
Step 4 (FALLBACK): WebSearch for employers that failed steps 1-3 (~10-20%).

Usage:
    from employers.identify_websites import identify_websites
    results = identify_websites(employers)
    # results: list of dicts with "website" set or "_remove" flagged
"""

from __future__ import annotations

import json
import logging
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logger = logging.getLogger(__name__)

# Gemini batch size for URL prediction/verification
_BATCH_SIZE = 150

# HTTP fetch config
_FETCH_WORKERS = 20
_FETCH_TIMEOUT = 20
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Parked domain signals
_PARKED_SIGNALS = [
    "domain for sale", "buy this domain", "sedoparking", "hugedomains",
    "godaddy", "afternic", "domain parking", "this domain is for sale",
    "parkingcrew", "sedo.com",
]


def identify_websites(
    employers: list[dict],
    region_display: str = "",
) -> list[dict]:
    """Run the full Predict → Fetch → Verify → Fallback pipeline.

    Each employer dict should have: name, sector, city, county, naics_label,
    size_class (from EDD). Returns the same list with "website" set on
    verified employers and "_remove" set on those with no web presence.
    """
    # Skip employers that already have a website
    need = [e for e in employers if not e.get("website")]
    if not need:
        logger.info("  All employers already have websites")
        return employers

    logger.info(f"  Identifying websites for {len(need)} employers")

    # Step 1: Predict
    predictions = _step_predict(need, region_display)

    # Step 2: Fetch
    fetched = _step_fetch(predictions)

    # Step 3: Verify
    verified, failures = _step_verify(need, predictions, fetched, region_display)

    # Apply verified URLs
    for emp in need:
        url = verified.get(emp["name"])
        if url:
            emp["website"] = url

    # Step 4: Fallback for failures
    if failures:
        logger.info(f"  Step 4 (fallback): {len(failures)} employers need WebSearch")
        fallback_results = _step_fallback(failures, region_display)
        for emp in need:
            if emp["name"] in fallback_results:
                result = fallback_results[emp["name"]]
                if result == "REMOVE":
                    emp["_remove"] = True
                elif result:
                    emp["website"] = result

    # Mark remaining no-website employers for removal
    for emp in need:
        if not emp.get("website") and not emp.get("_remove"):
            emp["_remove"] = True

    with_url = sum(1 for e in need if e.get("website"))
    removed = sum(1 for e in need if e.get("_remove"))
    logger.info(f"  Website identification complete: {with_url} verified, {removed} removed")

    return employers


# ── Step 1: Predict ──────────────────────────────────────────────────────

def _step_predict(employers: list[dict], region_display: str) -> dict[str, str]:
    """Gemini predicts candidate URLs using full EDD context."""
    logger.info(f"  Step 1 (predict): {len(employers)} employers")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("  No GEMINI_API_KEY — skipping prediction")
        return {}

    from google import genai
    client = genai.Client(api_key=api_key)

    all_predictions: dict[str, str] = {}

    for i in range(0, len(employers), _BATCH_SIZE):
        batch = employers[i:i + _BATCH_SIZE]
        lines = []
        for e in batch:
            city = e.get("city", "")
            county = e.get("county", "")
            naics = e.get("naics_label", e.get("sector", ""))
            size = e.get("size_class", "")
            lines.append(f"- {e['name']} | {city}, {county} County | {naics} | {size}")

        prompt = (
            f"For each employer below in the {region_display or 'California'} region, "
            "predict the most likely official website URL.\n\n"
            "IMPORTANT — use the city, county, and industry to disambiguate:\n"
            "- A 'Summit Healthcare' in San Bernardino County is NOT the same as "
            "'Summit Healthcare' in Arizona\n"
            "- A 'Premier Plumbing' in Riverside is NOT 'Premier Plumbing' in Texas\n"
            "- Use the NAICS industry to confirm the right company\n\n"
            "Rules:\n"
            "- Government entities: use .gov or .org domain\n"
            "- Education: use .edu domain\n"
            "- Healthcare systems: use the system's domain\n"
            "- Return NONE if the business is too small/local to have a website\n"
            "- Return NONE rather than guess — a wrong URL is worse than no URL\n\n"
            "Return JSON only: {\"employer_name\": \"https://...\" or \"NONE\"}\n"
            "No markdown fences.\n\n"
            "EMPLOYERS:\n" + "\n".join(lines)
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
            )
            text = _strip_markdown(response.text)
            preds = json.loads(text)
            all_predictions.update(preds)
            logger.info(f"    Batch {i // _BATCH_SIZE + 1}: {len(preds)} predictions")
        except Exception as e:
            logger.error(f"    Batch {i // _BATCH_SIZE + 1} failed: {e}")

    predicted = sum(1 for v in all_predictions.values() if v and v != "NONE")
    logger.info(f"  Step 1 complete: {predicted} URLs predicted, "
                f"{len(all_predictions) - predicted} NONE")
    return all_predictions


# ── Step 2: Fetch ────────────────────────────────────────────────────────

def _step_fetch(predictions: dict[str, str]) -> dict[str, dict]:
    """Parallel HTTP GET to retrieve page content from candidate URLs."""
    urls_to_fetch = {
        name: url for name, url in predictions.items()
        if url and url != "NONE" and url.startswith("http")
    }
    logger.info(f"  Step 2 (fetch): {len(urls_to_fetch)} URLs to verify")

    results: dict[str, dict] = {}

    def fetch_one(name: str, url: str) -> tuple[str, dict]:
        try:
            r = requests.get(
                url, timeout=_FETCH_TIMEOUT, allow_redirects=True, verify=False,
                headers={"User-Agent": _USER_AGENT, "Accept": "text/html"},
            )
            if r.status_code >= 400:
                return name, {"status": "BLOCKED", "code": r.status_code, "url": url}

            text = r.text[:5000]
            text_lower = text.lower()

            # Check for parked domains
            if any(signal in text_lower for signal in _PARKED_SIGNALS):
                return name, {"status": "PARKED", "url": url}

            # Extract readable content for verification
            # Strip HTML tags for a rough text extraction
            clean = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r'<[^>]+>', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()[:2000]

            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else ""

            return name, {
                "status": "OK",
                "url": r.url,  # final URL after redirects
                "title": title,
                "content": clean,
            }
        except requests.exceptions.ConnectionError:
            return name, {"status": "CONN_ERROR", "url": url}
        except requests.exceptions.Timeout:
            return name, {"status": "TIMEOUT", "url": url}
        except Exception as e:
            return name, {"status": "ERROR", "url": url, "error": str(e)[:100]}

    with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as executor:
        futures = {
            executor.submit(fetch_one, name, url): name
            for name, url in urls_to_fetch.items()
        }
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result

    ok = sum(1 for r in results.values() if r["status"] == "OK")
    blocked = sum(1 for r in results.values() if r["status"] in ("BLOCKED", "CONN_ERROR", "TIMEOUT"))
    bad = sum(1 for r in results.values() if r["status"] in ("PARKED", "ERROR"))
    logger.info(f"  Step 2 complete: {ok} fetched, {blocked} blocked, {bad} parked/error")
    return results


# ── Step 3: Verify ───────────────────────────────────────────────────────

def _step_verify(
    employers: list[dict],
    predictions: dict[str, str],
    fetched: dict[str, dict],
    region_display: str,
) -> tuple[dict[str, str], list[dict]]:
    """Gemini verifies fetched page content matches the employer."""
    logger.info(f"  Step 3 (verify): checking page content against employer identity")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Can't verify — return predictions as-is for employers with OK fetches
        verified = {}
        failures = []
        for emp in employers:
            fetch = fetched.get(emp["name"], {})
            if fetch.get("status") == "OK":
                verified[emp["name"]] = predictions.get(emp["name"], "")
            else:
                failures.append(emp)
        return verified, failures

    from google import genai
    client = genai.Client(api_key=api_key)

    # Build verification batches: only employers with fetched content
    to_verify = []
    no_content = []  # blocked/failed/no-prediction — go to fallback

    for emp in employers:
        name = emp["name"]
        fetch = fetched.get(name, {})
        pred = predictions.get(name, "NONE")

        if pred == "NONE" or not pred:
            no_content.append(emp)
        elif fetch.get("status") == "OK":
            to_verify.append((emp, fetch))
        elif fetch.get("status") == "PARKED":
            no_content.append(emp)  # parked → fallback
        elif fetch.get("status") in ("BLOCKED", "CONN_ERROR", "TIMEOUT"):
            # Can't verify content — accept on trust but mark as unverified
            to_verify.append((emp, fetch))
        else:
            no_content.append(emp)

    verified: dict[str, str] = {}
    failures: list[dict] = list(no_content)

    for i in range(0, len(to_verify), _BATCH_SIZE):
        batch = to_verify[i:i + _BATCH_SIZE]
        lines = []
        for emp, fetch in batch:
            url = predictions.get(emp["name"], "")
            city = emp.get("city", "")
            county = emp.get("county", "")
            naics = emp.get("naics_label", emp.get("sector", ""))

            if fetch.get("status") == "OK":
                title = fetch.get("title", "")
                content = fetch.get("content", "")[:800]
                page_info = f"Title: {title}\nContent preview: {content}"
            else:
                page_info = f"(Could not access page — {fetch.get('status', 'unknown')})"

            lines.append(
                f"EMPLOYER: {emp['name']}\n"
                f"  Location: {city}, {county} County, CA\n"
                f"  Industry: {naics}\n"
                f"  Predicted URL: {url}\n"
                f"  Page info: {page_info}\n"
            )

        prompt = (
            "For each employer below, verify whether the predicted URL belongs to "
            "this SPECIFIC employer in this SPECIFIC location and industry.\n\n"
            "Return one of:\n"
            "- MATCH: the page clearly belongs to this employer (or its parent company)\n"
            "- WRONG: the page belongs to a DIFFERENT company with a similar name\n"
            "- ACCEPT: the page was blocked but the URL pattern is credible "
            "(e.g., .gov, .edu, major brand domain)\n"
            "- REJECT: the page was blocked AND the URL looks suspicious\n\n"
            "Return JSON: {\"employer_name\": \"MATCH\" or \"WRONG\" or \"ACCEPT\" or \"REJECT\"}\n"
            "No markdown fences.\n\n"
            + "\n---\n".join(lines)
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
            )
            text = _strip_markdown(response.text)
            verdicts = json.loads(text)

            for emp, fetch in batch:
                verdict = verdicts.get(emp["name"], "REJECT")
                url = predictions.get(emp["name"], "")

                if verdict in ("MATCH", "ACCEPT"):
                    # Use the final URL (after redirects) if available
                    final_url = fetch.get("url", url) if fetch.get("status") == "OK" else url
                    verified[emp["name"]] = final_url
                else:
                    failures.append(emp)

            match_ct = sum(1 for v in verdicts.values() if v in ("MATCH", "ACCEPT"))
            wrong_ct = sum(1 for v in verdicts.values() if v == "WRONG")
            reject_ct = sum(1 for v in verdicts.values() if v == "REJECT")
            logger.info(
                f"    Verify batch {i // _BATCH_SIZE + 1}: "
                f"{match_ct} match, {wrong_ct} wrong, {reject_ct} reject"
            )
        except Exception as e:
            logger.error(f"    Verify batch {i // _BATCH_SIZE + 1} failed: {e}")
            failures.extend(emp for emp, _ in batch)

    logger.info(f"  Step 3 complete: {len(verified)} verified, {len(failures)} to fallback")
    return verified, failures


# ── Step 4: Fallback ─────────────────────────────────────────────────────

def _step_fallback(
    failures: list[dict],
    region_display: str,
) -> dict[str, str | None]:
    """Gemini-powered search fallback for employers that failed steps 1-3."""
    logger.info(f"  Step 4 (fallback): {len(failures)} employers")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {e["name"]: "REMOVE" for e in failures}

    from google import genai
    client = genai.Client(api_key=api_key)

    results: dict[str, str | None] = {}

    for i in range(0, len(failures), _BATCH_SIZE):
        batch = failures[i:i + _BATCH_SIZE]
        lines = []
        for emp in batch:
            city = emp.get("city", "")
            county = emp.get("county", "")
            naics = emp.get("naics_label", emp.get("sector", ""))
            size = emp.get("size_class", "")
            lines.append(f"- {emp['name']} | {city}, {county} County | {naics} | {size}")

        prompt = (
            "For each employer below, I was unable to find or verify their website "
            "through URL prediction. These are employers from EDD's ALMIS database "
            f"in the {region_display or 'California'} region.\n\n"
            "For each, decide:\n"
            "1. If you KNOW this employer's official website URL with high confidence, "
            "return it.\n"
            "2. If this employer is too small, is a labor contractor, is a "
            "sub-department, or is not a viable CTE partnership target, return \"REMOVE\".\n"
            "3. If you genuinely cannot determine the website, return \"REMOVE\" — "
            "an employer without discoverable web presence is not a partnership target.\n\n"
            "Return JSON: {\"employer_name\": \"https://...\" or \"REMOVE\"}\n"
            "No markdown fences.\n\n"
            "EMPLOYERS:\n" + "\n".join(lines)
        )

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt,
            )
            text = _strip_markdown(response.text)
            preds = json.loads(text)
            for name, val in preds.items():
                if val and val.startswith("http"):
                    results[name] = val
                else:
                    results[name] = "REMOVE"
            removed = sum(1 for v in preds.values() if v == "REMOVE" or not v or not str(v).startswith("http"))
            logger.info(f"    Fallback batch {i // _BATCH_SIZE + 1}: "
                        f"{len(preds) - removed} URLs, {removed} removed")
        except Exception as e:
            logger.error(f"    Fallback batch {i // _BATCH_SIZE + 1} failed: {e}")
            for emp in batch:
                results[emp["name"]] = "REMOVE"

    return results


# ── Helpers ──────────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Strip markdown code fences from Gemini response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0] if "\n" in text else text[:-3]
    if text.startswith("json"):
        text = text[4:].strip()
    return text.strip()
