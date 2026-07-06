"""UserRepository interface.

Describes the persistence operations the domain needs for users.
Implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.user import User


class UserRepository(ABC):
    """Abstraction over user persistence."""

    @abstractmethod
    async def add(self, user: User) -> None:
        """Persist a new user."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """Return the user with the given id, or None."""

    @abstractmethod
    async def update(self, user: User) -> None:
        """Persist changes to an existing user."""

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """Remove a user by id."""
