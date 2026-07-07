"""Tests for SupabaseJwtVerifier.

Seeds the fake CachePort with a real JWKS (built from a locally-generated RSA
key) so `verify()` never has to hit the network — the injected HTTP client
raises if it's ever called, proving the cache-hit path skips the fetch.
"""

from __future__ import annotations

import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from src.application.ports.token_verifier_port import InvalidTokenError
from src.infrastructure.auth.supabase_jwt_verifier import SupabaseJwtVerifier
from tests.fakes.in_memory_cache_port import InMemoryCachePort

SUPABASE_URL = "https://proj.supabase.co"
AUDIENCE = "authenticated"
ISSUER = f"{SUPABASE_URL}/auth/v1"
KID = "test-kid"
USER_ID = "11111111-1111-1111-1111-111111111111"


class _ExplodingHttpClient:
    """Stands in for httpx.AsyncClient — fails the test if verify() ever
    tries to fetch the JWKS instead of using the seeded cache."""

    async def get(self, url: str) -> object:
        raise AssertionError(f"Unexpected JWKS fetch to {url}")


def _generate_keypair() -> tuple[object, dict[str, object]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk["kid"] = KID
    jwk["alg"] = "RS256"
    jwk["use"] = "sig"
    return private_key, jwk


async def _seeded_verifier(jwk: dict[str, object]) -> SupabaseJwtVerifier:
    cache = InMemoryCachePort()
    await cache.set("supabase:jwks", json.dumps({"keys": [jwk]}))
    return SupabaseJwtVerifier(
        supabase_url=SUPABASE_URL,
        audience=AUDIENCE,
        cache=cache,
        http_client=_ExplodingHttpClient(),  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_verifies_a_valid_token_and_returns_the_subject() -> None:
    private_key, jwk = _generate_keypair()
    token = jwt.encode(
        {"sub": USER_ID, "aud": AUDIENCE, "iss": ISSUER},
        private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    verifier = await _seeded_verifier(jwk)

    assert await verifier.verify(token) == USER_ID


@pytest.mark.asyncio
async def test_bad_signature_raises_invalid_token_error() -> None:
    _, jwk = _generate_keypair()
    other_private_key, _ = _generate_keypair()
    token = jwt.encode(
        {"sub": USER_ID, "aud": AUDIENCE, "iss": ISSUER},
        other_private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    verifier = await _seeded_verifier(jwk)

    with pytest.raises(InvalidTokenError):
        await verifier.verify(token)


@pytest.mark.asyncio
async def test_wrong_audience_raises_invalid_token_error() -> None:
    private_key, jwk = _generate_keypair()
    token = jwt.encode(
        {"sub": USER_ID, "aud": "not-authenticated", "iss": ISSUER},
        private_key,
        algorithm="RS256",
        headers={"kid": KID},
    )
    verifier = await _seeded_verifier(jwk)

    with pytest.raises(InvalidTokenError):
        await verifier.verify(token)
