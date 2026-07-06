"""GetUserProfile use case.

Fetches a user's current taste profile — used to prefill the editable
profile settings screen (§6).
"""

from __future__ import annotations

from src.application.dtos.user_dtos import UserProfileOutput
from src.application.mappers.user_mapper import UserMapper
from src.domain.exceptions import UserNotFoundError
from src.domain.repositories.user_repository import UserRepository


class GetUserProfileUseCase:
    """Fetch a user's hard constraints, soft preferences, and taste vector."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: str) -> UserProfileOutput:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserMapper.to_output(user)
