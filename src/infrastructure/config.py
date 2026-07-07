"""Environment-driven configuration.

Environment variables are read here (and only here) per the layer contract.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    app_env: str
    recipe_tagging_model: str
    recipe_tagging_batch_poll_seconds: float
    supabase_url: str
    supabase_jwt_audience: str
    supabase_jwks_cache_ttl_seconds: float

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://shelflife:shelflife@localhost:5432/shelflife",
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            app_env=os.getenv("APP_ENV", "development"),
            # ANTHROPIC_API_KEY is read by the Anthropic SDK itself, not here —
            # only the model choice is our own config surface (the batch job
            # is a cost-sensitive, non-latency-sensitive run, so ops may want
            # to point it at a cheaper model without a code change).
            recipe_tagging_model=os.getenv("RECIPE_TAGGING_MODEL", "claude-opus-4-8"),
            recipe_tagging_batch_poll_seconds=float(
                os.getenv("RECIPE_TAGGING_BATCH_POLL_SECONDS", "30")
            ),
            # SUPABASE_URL is the project's base URL (e.g.
            # https://xyzcompany.supabase.co) — the JWKS endpoint used to
            # verify Auth JWTs is derived from it, not configured separately.
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_jwt_audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated"),
            supabase_jwks_cache_ttl_seconds=float(
                os.getenv("SUPABASE_JWKS_CACHE_TTL_SECONDS", "3600")
            ),
        )


settings = Settings.from_env()
