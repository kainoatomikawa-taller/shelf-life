"""UpdateProfile use case.

Backs the Profile screen's editable display_name and username. Username
changes are unlimited with no cooldown, but every actual change re-runs the
case-insensitive uniqueness check — a plain DB unique constraint on the
already-normalized column is the backstop against a concurrent race.
"""

from __future__ import annotations

from src.application.dtos.profile_dtos import ProfileOutput, UpdateProfileInput
from src.application.mappers.profile_mapper import ProfileMapper
from src.domain.exceptions import ProfileNotFoundError, UsernameAlreadyTakenError
from src.domain.repositories.profile_repository import ProfileRepository


class UpdateProfileUseCase:
    """Update the caller's display name and/or username."""

    def __init__(self, repository: ProfileRepository) -> None:
        self._repository = repository

    async def execute(self, dto: UpdateProfileInput) -> ProfileOutput:
        profile = await self._repository.get_by_id(dto.user_id)
        if profile is None:
            raise ProfileNotFoundError(dto.user_id)

        if dto.username is not None:
            normalized_username = dto.username.strip().lower()
            if normalized_username != profile.username:
                existing = await self._repository.get_by_username(
                    normalized_username
                )
                if existing is not None and existing.id != profile.id:
                    raise UsernameAlreadyTakenError(normalized_username)
                profile.update_username(dto.username)

        if dto.display_name is not None:
            profile.update_display_name(dto.display_name)

        await self._repository.update(profile)
        return ProfileMapper.to_output(profile)
