"""In-memory RatingRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.rating import Rating
from src.domain.repositories.rating_repository import RatingRepository


class InMemoryRatingRepository(RatingRepository):
    def __init__(self) -> None:
        self._ratings: dict[str, Rating] = {}

    async def add(self, rating: Rating) -> None:
        self._ratings[rating.id] = rating

    async def list_by_user(self, user_id: str) -> list[Rating]:
        return [r for r in self._ratings.values() if r.user_id == user_id]
