"""URL-liveness audit for employer records.

Scans every loadable employer's website with a real HTTP request that
mimics a browser, then applies a binary include/exclude rule:

    URL returns 404 or 410     → BROKEN. Try research; on failure, drop.
    URL returns 2xx/3xx        → OK. No action.
    Anything else              → UNKNOWN. No action.

Conservatism is deliberate. 403 from anti-bot fronts (Cloudflare, Akamai)
and 5xx/SSL/timeout errors don't reliably indicate that a real user
clicking the link will see a broken page. Only 404/410 — "the page is
gone" — is treated as actionable. Everything else is left untouched.

The "rest of the employer set remains untouched" principle: only
employers with broken URLs are touched. Description, occupations, sector,
and identity_verified flag are preserved on URL rotation. On exclusion,
the employer is moved to dropped.jsonl with reason 'url_rotted', the
same audit-trail mechanism the enrichment pipeline uses.

Usage:
    python3 -m employers.audit_url_liveness --dry-run
    python3 -m employers.audit_url_liveness
    python3 -m employers.audit_url_liveness --region FN
    python3 -m employers.audit_url_liveness --no-research  # drop broken without trying to find alternatives
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).parent
EMPLOYERS_PATH = _THIS_DIR / "employers.json"
DROPPED_LOG = _THIS_DIR / "dropped.jsonl"

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
_TIMEOUT = 10
_CHECK_CONCURRENCY = 20

# Status codes that are definitively "page is gone." Only these trigger
# the broken-URL path. Other 4xx (403 in particular) are common false
# positives from bot-fronting and don't reliably indicate broken pages.
_BROKEN_STATUSES = frozenset({404, 410})

# Auth-wall hosts: when an employer URL redirects to one of these, the
# real public page is gated behind employee SSO and the user clicking the
# atlas link sees a sign-in form, not the company's site. These employers
# don't have a public-accessible web presence and should be dropped.
_AUTH_WALL_HOSTS = frozenset({
    "login.microsoftonline.com",
    "login.salesforce.com",
    "accounts.google.com",
    "auth.okta.com",
    "okta.com",  # subdomain matching handled separately
    "login.adp.com",
    "workday.com",
    "myworkday.com",
    "signin.aws.amazon.com",
    "auth0.com",
    "auth.pingone.com",
    "login.live.com",
    "secureauth.com",
})

# Body length below this threshold (in bytes) signals a dead/parked page.
# Real corporate homepages are typically tens of kilobytes minimum once
# you account for boilerplate <head>, navigation, and meta tags. A 200
# OK with < 500 bytes is essentially an empty response.
_MIN_BODY_BYTES = 500


def _is_loadable(emp: dict) -> bool:
    """Mirror of load.py's filter — only audit URLs that would actually load."""
    if not emp.get("enrichment_attempted"):
        return True
    if not emp.get("identity_verified"):
        return False
    return emp.get("enrichment_promoted") is True


def _final_host_is_auth_wall(final_url: str) -> bool:
    """Check whether the redirect terminus is a known SSO/auth provider."""
    try:
        from urllib.parse import urlparse
        host = (urlparse(final_url).hostname or "").lower()
    except Exception:
        return False
    if not host:
        return False
    # Direct host match
    if host in _AUTH_WALL_HOSTS:
        return True
    # Suffix match for subdomains (e.g., something.okta.com)
    for auth_host in _AUTH_WALL_HOSTS:
        if host.endswith("." + auth_host) or host == auth_host:
            return True
    return False


def _check_url(url: str) -> tuple[str, str | None, int | str | None]:
    """Returns (status, final_url, http_code).

    status: 'ok' | 'broken' | 'unknown'
    final_url: terminal URL after redirects, or None
    http_code: integer status code; or label like 'timeout'/'ssl'/'auth_wall'/'empty_body'

    A URL is broken if any of:
      - Final HTTP status is 404 or 410 (page gone)
      - Final URL after redirects lands on a known SSO/auth host
        (the public can't access the employer's site without login)
      - GET response body is empty or below _MIN_BODY_BYTES (dead/parked)

    The body-length check fires only when status is 2xx/3xx — if HEAD
    already gave 4xx/5xx, that's reported on its own.
    """
    headers = {"User-Agent": _BROWSER_UA}
    try:
        r = requests.head(
            url, timeout=_TIMEOUT, allow_redirects=True, verify=False,
            headers=headers,
        )
        code = r.status_code
        final_url = r.url

        # Early-exit on hard 404/410 from HEAD.
        if code in _BROKEN_STATUSES:
            return ("broken", final_url, code)

        # Auth-wall detection: if redirects land on an SSO host, the
        # employer's public site is gated behind login.
        if code < 400 and _final_host_is_auth_wall(final_url):
            return ("broken", final_url, "auth_wall")

        if code < 400:
            # Body-length sanity check: a 200 OK with empty/tiny body is
            # a parked or dead site. Gated on status 200 specifically
            # because:
            #   - 202 Accepted = bot-challenge response (Cloudflare,
            #     etc.) where the body is a small JS payload that a
            #     real browser executes to get the real page
            #   - 204 No Content / 205 Reset = expected-empty by spec
            #   - 3xx is already handled by allow_redirects
            try:
                r2 = requests.get(
                    url, timeout=_TIMEOUT, allow_redirects=True, verify=False,
                    headers={**headers, "Range": "bytes=0-2047"},
                )
                # Re-check auth-wall after GET (HEAD-only redirects may differ from GET).
                if _final_host_is_auth_wall(r2.url):
                    return ("broken", r2.url, "auth_wall")
                body_len = len(r2.content or b"")
                if r2.status_code == 200 and body_len < _MIN_BODY_BYTES:
                    return ("broken", r2.url, "empty_body")
            except Exception:
                # If GET fails when HEAD succeeded, fall through to ok
                # (don't flap on transient GET issues).
                pass
            return ("ok", final_url, code)

        # 4xx/5xx that isn't 404/410 — many servers reject HEAD but accept
        # GET. Confirm with GET before declaring unknown.
        r2 = requests.get(
            url, timeout=_TIMEOUT, allow_redirects=True, verify=False,
            headers=headers, stream=True,
        )
        r2.close()
        if r2.status_code in _BROKEN_STATUSES:
            return ("broken", r2.url, r2.status_code)
        if r2.status_code < 400:
            if _final_host_is_auth_wall(r2.url):
                return ("broken", r2.url, "auth_wall")
            return ("ok", r2.url, r2.status_code)
        return ("unknown", None, r2.status_code)
    except requests.exceptions.SSLError:
        return ("unknown", None, "ssl")
    except requests.exceptions.Timeout:
        return ("unknown", None, "timeout")
    except requests.exceptions.ConnectionError:
        return ("unknown", None, "connection")
    except Exception as e:
        return ("unknown", None, f"err:{type(e).__name__}")


async def _gemini_verify(client, types, url: str, employer_name: str) -> str:
    """Ask Gemini whether the URL serves real, public-accessible business
    content. Returns 'ok', 'broken', or 'unknown'.

    Used as escalation when CLI HTTP probing returns 'unknown' (connection
    error, timeout, SSL — could be anti-bot blocking us specifically OR
    a genuinely-dead site; CLI can't tell). Gemini's url_context fetches
    via Google's whitelisted infrastructure, which most anti-bot
    fronts permit. So Gemini's success/failure is a stronger signal of
    'is this URL real?' than our CLI probe's failure alone.
    """
    prompt = (
        f"Read the page at {url} and report what you find. "
        "If the page is dead, parked, empty, or only shows an error or "
        "challenge with no real content, respond exactly: BROKEN\n"
        "If the page serves real public business content, respond exactly: OK\n"
        "If you cannot determine either way, respond exactly: UNKNOWN\n"
        "Output only one of those three tokens. No prose, no JSON."
    )
    config = types.GenerateContentConfig(
        tools=[types.Tool(url_context=types.UrlContext())],
        temperature=0.0,
    )
    try:
        r = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )
        text = (r.text or "").strip().upper()
        if "OK" in text and "BROKEN" not in text:
            return "ok"
        if "BROKEN" in text:
            return "broken"
        return "unknown"
    except Exception as e:
        logger.warning(f"  gemini_verify({employer_name}) failed: {e}")
        return "unknown"


async def _try_find_replacement(client, types, employer: dict) -> str | None:
    """Try to find a live replacement URL for an employer with a broken URL.

    Uses the existing research path from enrich.py for consistency. Validates
    that any candidate URL is actually live (binary check) before accepting.
    Returns the new URL on success, else None.
    """
    from employers.enrich import _research_url_async

    prior_url = employer["website"]
    action, new_url = await _research_url_async(
        client, types, employer, prior_url, label=f"audit:{employer['name'][:30]}",
    )
    if action != "url" or not new_url:
        return None
    # Validate: the proposed alternative must itself be live (otherwise
    # we'd just rotate from one broken URL to another).
    status, _final, _code = _check_url(new_url)
    if status != "ok":
        logger.info(f"  research proposed {new_url} but it returned {_code} — rejecting")
        return None
    return new_url


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _append_dropped(entry: dict, dry_run: bool) -> None:
    """Append to dropped.jsonl. No-op under dry-run so audit logs stay
    authoritative — only real runs leave a paper trail."""
    if dry_run:
        return
    with open(DROPPED_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


async def audit(
    region: str | None = None,
    research: bool = True,
    dry_run: bool = False,
) -> dict:
    warnings.filterwarnings("ignore")
    with open(EMPLOYERS_PATH) as f:
        employers = json.load(f)

    targets = [e for e in employers if _is_loadable(e) and e.get("website")]
    if region:
        targets = [e for e in targets if region in e.get("regions", [])]

    logger.info(f"Auditing {len(targets)} URLs (region={region}, research={research})")

    # ── Stage 1: parallel liveness check ─────────────────────────────────
    def check(emp: dict) -> tuple[dict, str, str | None, int | str | None]:
        status, final, code = _check_url(emp["website"])
        return (emp, status, final, code)

    broken: list[tuple[dict, str | None, int | str | None]] = []
    ok_count = 0
    unknown: list[tuple[dict, str | int | None]] = []
    with ThreadPoolExecutor(max_workers=_CHECK_CONCURRENCY) as ex:
        for emp, status, final, code in ex.map(check, targets):
            if status == "ok":
                ok_count += 1
            elif status == "broken":
                broken.append((emp, final, code))
            else:
                unknown.append((emp, code))

    logger.info(
        f"Liveness (CLI probe): {ok_count} ok, {len(broken)} broken, "
        f"{len(unknown)} unknown"
    )

    # Need a Gemini client for both the unknown-escalation and the
    # broken-URL research path. Set up once.
    client = None
    types = None
    if research:
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            from google import genai
            from google.genai import types as _types
            client = genai.Client(api_key=api_key)
            types = _types
        else:
            logger.warning("No GEMINI_API_KEY — skipping verify+research")

    # ── Stage 1.5: Gemini-verify the unknown set ─────────────────────────
    # CLI 'unknown' (connection error, timeout, SSL) is ambiguous: could
    # be anti-bot blocking us specifically (real site, browser users see
    # it fine) OR a genuinely-dead site. Gemini's url_context fetches via
    # Google's whitelisted infrastructure, which most anti-bot fronts
    # permit. So Gemini's verdict converts ambiguity into 'ok' or
    # 'broken'. Without this step, dead sites like Spartan Moving stay
    # in production because our CLI can't tell them apart from
    # bot-fronted real sites like Foster Farms.
    unknown_ok = 0
    unknown_still_unclear = 0
    if client is not None and unknown:
        logger.info(f"Gemini-verifying {len(unknown)} CLI-unknown URLs")
        for emp, code in unknown:
            verdict = await _gemini_verify(client, types, emp["website"], emp["name"])
            if verdict == "ok":
                unknown_ok += 1
            elif verdict == "broken":
                broken.append((emp, emp["website"], "gemini_verify_broken"))
                logger.info(f"  Gemini-verify: {emp['name']} → broken (CLI was {code})")
            else:
                unknown_still_unclear += 1
        logger.info(
            f"Gemini-verify: {unknown_ok} confirmed ok, "
            f"{len(broken) - (len(broken) - sum(1 for _,_,c in broken if c == 'gemini_verify_broken'))} "
            f"escalated to broken, {unknown_still_unclear} still unclear"
        )
    else:
        # No Gemini available; treat all unknowns as keep (current behavior).
        unknown_still_unclear = len(unknown)

    if not broken:
        return {
            "targets": len(targets),
            "ok": ok_count + unknown_ok,
            "broken": 0,
            "unknown": unknown_still_unclear,
            "rotated": 0,
            "dropped": 0,
        }

    # ── Stage 2: research replacements for broken URLs ───────────────────
    rotated = 0
    drop_set: set[str] = set()

    for emp, final, code in broken:
        prior_url = emp["website"]
        replacement: str | None = None
        if client is not None:
            try:
                replacement = await _try_find_replacement(client, types, emp)
            except Exception as e:
                logger.warning(f"  research error for {emp['name']}: {e}")

        if replacement:
            logger.info(
                f"  ✓ {emp['name']}: rotated "
                f"{prior_url} → {replacement}"
            )
            emp["website"] = replacement
            rotated += 1
        else:
            logger.info(
                f"  ✗ {emp['name']}: dropped (no working alternative; "
                f"prior URL returned {code})"
            )
            drop_set.add(emp["name"])
            _append_dropped({
                "name": emp["name"],
                "status": "dropped_url_rotted",
                "reason": f"url returned {code}; no working replacement found",
                "prior_url": prior_url,
                "regions": emp.get("regions", []),
                "sector": emp.get("sector"),
                "dropped_at": _now_iso(),
            }, dry_run=dry_run)

    # ── Stage 3: write back ──────────────────────────────────────────────
    kept = [e for e in employers if e["name"] not in drop_set]

    if not dry_run:
        with open(EMPLOYERS_PATH, "w") as f:
            json.dump(kept, f, indent=2)

    return {
        "targets": len(targets),
        "ok": ok_count + unknown_ok,
        "broken": len(broken),
        "unknown": unknown_still_unclear,
        "rotated": rotated,
        "dropped": len(drop_set),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit URL liveness; rotate or drop broken URLs."
    )
    parser.add_argument("--region", type=str, default=None,
                        help="Limit audit to employers tagged with this COE region")
    parser.add_argument("--no-research", action="store_true",
                        help="Drop broken URLs without trying to find alternatives")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report findings without writing employers.json")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    stats = asyncio.run(audit(
        region=args.region,
        research=not args.no_research,
        dry_run=args.dry_run,
    ))

    print("=" * 60)
    print("URL LIVENESS AUDIT" + (" (dry run)" if args.dry_run else ""))
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:12s}  {v}")


if __name__ == "__main__":
    main()
