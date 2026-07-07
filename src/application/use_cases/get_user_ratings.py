"""GetUserRatings use case.

Backs the session-launch auto-load: returns every rating a user has
recorded, most recent first, so the client can restore rating history
without a device-specific sync step.
"""

from __future__ import annotations

from src.application.dtos.rating_dtos import GetUserRatingsInput, RatingOutput
from src.application.mappers.rating_mapper import RatingMapper
from src.domain.exceptions import UserNotFoundError
from src.domain.repositories.rating_repository import RatingRepository
from src.domain.repositories.user_repository import UserRepository


class GetUserRatingsUseCase:
    """Return every rating a user has recorded."""

    def __init__(
        self,
        rating_repository: RatingRepository,
        user_repository: UserRepository,
    ) -> None:
        self._rating_repository = rating_repository
        self._user_repository = user_repository

    async def execute(self, dto: GetUserRatingsInput) -> list[RatingOutput]:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        ratings = await self._rating_repository.list_by_user(dto.user_id)
        ratings_by_recency = sorted(
            ratings, key=lambda rating: rating.made_it_at, reverse=True
        )
        return [RatingMapper.to_rating_output(rating) for rating in ratings_by_recency]
