"""OAuth resource-server token verifier: JWT/JWKS validation, provider-agnostic.

The MCP server validates authorization-server-issued access tokens as a resource
server. These tests pin that validation with a synthetic RSA-signed JWT — no
network, no provider: a correctly-signed token with matching issuer + audience
yields an AccessToken carrying the subject, scopes, and the raw claims (including
email, kept for later institution auto-scope), while a wrong-audience, wrong-
issuer, expired, or wrong-key token is rejected (None). This is exactly the trust
boundary that lets us delegate the OAuth flow to WorkOS and keep our server thin.

Coverage:
  - a correctly-signed token with matching iss/aud verifies -> AccessToken
  - the email claim is preserved in AccessToken.claims (for institution mapping)
  - wrong audience is rejected
  - wrong issuer is rejected
  - an expired token is rejected
  - a token signed by an unknown key is rejected
"""
from __future__ import annotations

import time

import anyio
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from mcp_server.auth import JwtTokenVerifier

ISS = "https://kallipolis.authkit.app"
AUD = "https://api.kallipolis.us/mcp-oauth"


def _keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, priv.public_key()


class _FakeJWK:
    def __init__(self, key):
        self.key = key


class _FakeJWKClient:
    """Stands in for PyJWKClient — returns a fixed public key without a network."""

    def __init__(self, pub):
        self._pub = pub

    def get_signing_key_from_jwt(self, token):
        return _FakeJWK(self._pub)


def _token(priv, *, iss=ISS, aud=AUD, exp_delta=3600, **extra):
    now = int(time.time())
    payload = {"iss": iss, "aud": aud, "sub": "user_123", "exp": now + exp_delta,
               "iat": now, "scope": "openid email", **extra}
    return jwt.encode(payload, priv, algorithm="RS256")


def _verify(pub, token):
    v = JwtTokenVerifier(issuer=ISS, audience=AUD, jwk_client=_FakeJWKClient(pub))
    return anyio.run(v.verify_token, token)


def test_valid_token_verifies():
    priv, pub = _keypair()
    at = _verify(pub, _token(priv, email="coord@smccd.edu"))
    assert at is not None
    assert at.subject == "user_123"
    assert "email" in at.scopes
    assert at.claims["email"] == "coord@smccd.edu"   # preserved for institution auto-scope
    assert at.resource == AUD


def test_wrong_audience_rejected():
    priv, pub = _keypair()
    assert _verify(pub, _token(priv, aud="https://evil.example/mcp")) is None


def test_wrong_issuer_rejected():
    priv, pub = _keypair()
    assert _verify(pub, _token(priv, iss="https://evil.example")) is None


def test_expired_token_rejected():
    priv, pub = _keypair()
    assert _verify(pub, _token(priv, exp_delta=-10)) is None


def test_unknown_signing_key_rejected():
    priv, _ = _keypair()
    _, other_pub = _keypair()
    assert _verify(other_pub, _token(priv)) is None
