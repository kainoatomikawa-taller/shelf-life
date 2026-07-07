"""CreateProfile use case.

Creates the public profile (username, display name) for an already
authenticated user — `user_id` is the verified `auth.users.id`, never a
client-supplied value. A user gets at most one profile, and usernames are
unique case-insensitively (enforced by normalization in the Profile entity
plus a unique constraint at the persistence layer).
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.application.dtos.profile_dtos import CreateProfileInput, ProfileOutput
from src.application.mappers.profile_mapper import ProfileMapper
from src.domain.entities.profile import Profile
from src.domain.exceptions import ProfileAlreadyExistsError, UsernameAlreadyTakenError
from src.domain.repositories.profile_repository import ProfileRepository


class CreateProfileUseCase:
    """Create a new profile for an authenticated user."""

    def __init__(self, repository: ProfileRepository) -> None:
        self._repository = repository

    async def execute(self, dto: CreateProfileInput) -> ProfileOutput:
        existing = await self._repository.get_by_id(dto.user_id)
        if existing is not None:
            raise ProfileAlreadyExistsError(dto.user_id)

        normalized_username = dto.username.strip().lower()
        if await self._repository.get_by_username(normalized_username) is not None:
            raise UsernameAlreadyTakenError(normalized_username)

        profile = Profile(
            id=dto.user_id,
            username=dto.username,
            display_name=dto.display_name,
            created_at=datetime.now(UTC),
            email=dto.email,
        )
        await self._repository.add(profile)
        return ProfileMapper.to_output(profile)
