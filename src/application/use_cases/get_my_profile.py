"""GetMyProfile use case.

Fetches the authenticated caller's own profile.
"""

from __future__ import annotations

from src.application.dtos.profile_dtos import ProfileOutput
from src.application.mappers.profile_mapper import ProfileMapper
from src.domain.exceptions import ProfileNotFoundError
from src.domain.repositories.profile_repository import ProfileRepository


class GetMyProfileUseCase:
    """Fetch the profile belonging to the authenticated user id."""

    def __init__(self, repository: ProfileRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: str) -> ProfileOutput:
        profile = await self._repository.get_by_id(user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)
        return ProfileMapper.to_output(profile)
