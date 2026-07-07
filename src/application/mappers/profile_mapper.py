"""Mapper between the Profile entity and its DTOs."""

from __future__ import annotations

from src.application.dtos.profile_dtos import ProfileOutput
from src.domain.entities.profile import Profile


class ProfileMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(profile: Profile) -> ProfileOutput:
        return ProfileOutput(
            id=profile.id,
            username=profile.username,
            display_name=profile.display_name,
            created_at=profile.created_at,
        )
