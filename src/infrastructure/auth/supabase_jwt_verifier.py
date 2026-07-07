"""Supabase implementation of TokenVerifierPort.

Verifies Supabase Auth JWTs against the project's JWKS endpoint
(``{supabase_url}/auth/v1/.well-known/jwks.json``), caching the key set via
CachePort so the JWKS isn't refetched on every request. On a cache hit with
an unknown ``kid`` (key rotation), it refetches once before giving up.
"""

from __future__ import annotations

import json

import httpx
import jwt

from src.application.ports.cache_port import CachePort
from src.application.ports.token_verifier_port import (
    InvalidTokenError,
    TokenVerifierPort,
)

_JWKS_CACHE_KEY = "supabase:jwks"


class SupabaseJwtVerifier(TokenVerifierPort):
    """Verifies Supabase Auth JWTs via the project's JWKS endpoint."""

    def __init__(
        self,
        supabase_url: str,
        audience: str,
        cache: CachePort,
        http_client: httpx.AsyncClient,
        cache_ttl_seconds: float = 3600,
    ) -> None:
        self._jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        self._issuer = f"{supabase_url}/auth/v1"
        self._audience = audience
        self._cache = cache
        self._http_client = http_client
        self._cache_ttl_seconds = cache_ttl_seconds

    async def verify(self, token: str) -> str:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Malformed token header.") from exc

        kid = header.get("kid")
        jwk = await self._find_key(kid)
        if jwk is None:
            raise InvalidTokenError(f"No matching signing key for kid '{kid}'.")

        try:
            signing_key = jwt.PyJWK(jwk).key
            payload = jwt.decode(
                token,
                key=signing_key,
                algorithms=[str(jwk.get("alg", "RS256"))],
                audience=self._audience,
                issuer=self._issuer,
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            raise InvalidTokenError("Token has no subject claim.")
        return sub

    # --- JWKS retrieval -------------------------------------------------

    async def _find_key(self, kid: object) -> dict[str, object] | None:
        keys = await self._get_jwks(force_refetch=False)
        match = next((k for k in keys if k.get("kid") == kid), None)
        if match is not None:
            return match
        # Unknown kid could mean the key set rotated since we cached it.
        keys = await self._get_jwks(force_refetch=True)
        return next((k for k in keys if k.get("kid") == kid), None)

    async def _get_jwks(self, force_refetch: bool) -> list[dict[str, object]]:
        if not force_refetch:
            cached = await self._cache.get(_JWKS_CACHE_KEY)
            if cached is not None:
                return self._parse_jwks(json.loads(cached))

        try:
            response = await self._http_client.get(self._jwks_url)
            response.raise_for_status()
            raw = response.json()
        except httpx.HTTPError as exc:
            raise InvalidTokenError("Could not reach the JWKS endpoint.") from exc

        await self._cache.set(
            _JWKS_CACHE_KEY,
            json.dumps(raw),
            ttl_seconds=int(self._cache_ttl_seconds),
        )
        return self._parse_jwks(raw)

    @staticmethod
    def _parse_jwks(payload: object) -> list[dict[str, object]]:
        if not isinstance(payload, dict):
            raise InvalidTokenError("Malformed JWKS response.")
        keys = payload.get("keys")
        if not isinstance(keys, list):
            raise InvalidTokenError("Malformed JWKS response.")
        return [key for key in keys if isinstance(key, dict)]
