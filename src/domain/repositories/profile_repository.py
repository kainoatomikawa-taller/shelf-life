"""ProfileRepository interface.

Describes the persistence operations the domain needs for profiles.
Implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.profile import Profile


class ProfileRepository(ABC):
    """Abstraction over profile persistence."""

    @abstractmethod
    async def add(self, profile: Profile) -> None:
        """Persist a new profile."""

    @abstractmethod
    async def get_by_id(self, profile_id: str) -> Profile | None:
        """Return the profile with the given id, or None."""

    @abstractmethod
    async def get_by_username(self, username: str) -> Profile | None:
        """Return the profile with the given (already-normalized) username,
        or None."""
