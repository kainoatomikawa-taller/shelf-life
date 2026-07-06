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

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://shelflife:shelflife@localhost:5432/shelflife",
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            app_env=os.getenv("APP_ENV", "development"),
        )


settings = Settings.from_env()
