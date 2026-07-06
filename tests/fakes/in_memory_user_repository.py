"""In-memory UserRepository for fast, isolated use case tests.

Demonstrates that use cases depend only on the domain interface, not on any
concrete database.
"""

from __future__ import annotations

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    async def add(self, user: User) -> None:
        self._users[user.id] = user

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    async def update(self, user: User) -> None:
        self._users[user.id] = user

    async def delete(self, user_id: str) -> None:
        self._users.pop(user_id, None)
