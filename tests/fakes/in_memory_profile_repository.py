"""In-memory ProfileRepository for fast, isolated use case tests.

Demonstrates that use cases depend only on the domain interface, not on any
concrete database.
"""

from __future__ import annotations

from src.domain.entities.profile import Profile
from src.domain.repositories.profile_repository import ProfileRepository


class InMemoryProfileRepository(ProfileRepository):
    def __init__(self) -> None:
        self._profiles: dict[str, Profile] = {}

    async def add(self, profile: Profile) -> None:
        self._profiles[profile.id] = profile

    async def get_by_id(self, profile_id: str) -> Profile | None:
        return self._profiles.get(profile_id)

    async def get_by_username(self, username: str) -> Profile | None:
        for profile in self._profiles.values():
            if profile.username == username:
                return profile
        return None
