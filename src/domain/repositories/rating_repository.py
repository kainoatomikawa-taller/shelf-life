"""RatingRepository interface.

Describes the persistence operations the domain needs, without committing to
any particular database or ORM. Implementations live in the infrastructure
layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.rating import Rating


class RatingRepository(ABC):
    """Abstraction over rating persistence."""

    @abstractmethod
    async def add(self, rating: Rating) -> None:
        """Persist a new rating."""

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[Rating]:
        """Return every rating the given user has recorded."""
