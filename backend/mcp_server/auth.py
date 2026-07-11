"""OAuth resource-server token verification.

The MCP server is a RESOURCE SERVER (MCP auth spec 2025-11-25): it does NOT run
the OAuth flow — an authorization server (WorkOS AuthKit) does. Our only job is
to validate the bearer access token the AS issued to the client: verify its
signature against the AS's JWKS, and that its issuer and audience are ours. The
mcp SDK then serves the RFC 9728 discovery metadata + the 401 challenge for us.

Deliberately provider-agnostic — standard JWT + JWKS (RFC 7515 / 7517 / 9068).
WorkOS is just the authorization server plugged in via env vars; swapping to any
compliant provider is a config change, not a rewrite.

Config (env):
  MCP_OAUTH_ISSUER    the AS issuer URL (e.g. the WorkOS AuthKit domain)
  MCP_OAUTH_AUDIENCE  our MCP URL, which the token's `aud` must equal (RFC 8707)
  MCP_OAUTH_JWKS_URL  the AS JWKS URL (defaults to <issuer>/oauth2/jwks)
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import jwt
from jwt import PyJWKClient

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

logger = logging.getLogger(__name__)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


class JwtTokenVerifier(TokenVerifier):
    """Validate an OAuth 2.1 access token (JWT) against the authorization
    server's JWKS. ``jwk_client`` is injectable so the validation is unit-tested
    without a network or a real provider."""

    def __init__(self, *, issuer: str, audience: str, jwks_url: Optional[str] = None,
                 jwk_client=None, algorithms=("RS256",)):
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.algorithms = list(algorithms)
        self._jwks = jwk_client or (PyJWKClient(jwks_url) if jwks_url else None)

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        if self._jwks is None:
            logger.warning("JwtTokenVerifier has no JWKS source; rejecting token")
            return None
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token, signing_key, algorithms=self.algorithms,
                audience=self.audience, issuer=self.issuer,
                options={"require": ["exp", "iss", "aud"]})
        except Exception as exc:  # bad signature / exp / aud / iss → not authorized
            logger.info("token rejected: %s", exc)
            return None
        scope = claims.get("scope", "")
        scopes = scope.split() if isinstance(scope, str) else list(scope or [])
        return AccessToken(
            token=token,
            client_id=str(claims.get("client_id") or claims.get("azp") or claims.get("cid") or ""),
            scopes=scopes,
            expires_at=claims.get("exp"),
            resource=self.audience,
            subject=claims.get("sub"),
            claims=claims,  # carries email/domain for later institution auto-scope
        )


def oauth_enabled() -> bool:
    """OAuth is active only when an issuer + audience are configured — so the
    server keeps its current behavior until we deliberately switch it on."""
    return bool(_env("MCP_OAUTH_ISSUER") and _env("MCP_OAUTH_AUDIENCE"))


def verifier_from_env() -> Optional[JwtTokenVerifier]:
    if not oauth_enabled():
        return None
    issuer = _env("MCP_OAUTH_ISSUER")
    audience = _env("MCP_OAUTH_AUDIENCE")
    jwks_url = _env("MCP_OAUTH_JWKS_URL") or f"{issuer.rstrip('/')}/oauth2/jwks"
    return JwtTokenVerifier(issuer=issuer, audience=audience, jwks_url=jwks_url)


def auth_settings_from_env() -> Optional[AuthSettings]:
    """The SDK AuthSettings that make FastMCP a resource server: it serves the
    RFC 9728 protected-resource metadata (pointing at the AS issuer) and the 401
    challenge. Returns None when OAuth is not configured."""
    if not oauth_enabled():
        return None
    from pydantic import AnyHttpUrl
    return AuthSettings(
        issuer_url=AnyHttpUrl(_env("MCP_OAUTH_ISSUER")),
        resource_server_url=AnyHttpUrl(_env("MCP_OAUTH_AUDIENCE")),
        required_scopes=None,
    )
