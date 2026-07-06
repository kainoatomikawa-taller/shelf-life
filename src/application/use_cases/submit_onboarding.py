"""SubmitOnboarding use case.

Creates or updates a user's hard constraints and soft preferences from the
onboarding flow (§5.1). Each step is optional — omitted fields fall back to
the domain defaults already encoded in HardConstraints/SoftPreferences, so a
fully-skipped onboarding still produces a valid user.
"""

from __future__ import annotations

from src.application.dtos.user_dtos import SubmitOnboardingInput, UserProfileOutput
from src.application.mappers.user_mapper import UserMapper
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.budget_sensitivity import BudgetSensitivity
from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences


class SubmitOnboardingUseCase:
    """Persist the taste profile collected during onboarding."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, dto: SubmitOnboardingInput) -> UserProfileOutput:
        hard_constraints = HardConstraints(
            allergies=dto.allergies,
            diet_type=DietType(dto.diet_type),
        )
        preferences = SoftPreferences(
            disliked_ingredients=dto.disliked_ingredients,
            liked_cuisines=dto.liked_cuisines,
            flavor_profile=FlavorProfile(
                sweetness=dto.flavor_profile.sweetness,
                saltiness=dto.flavor_profile.saltiness,
                sourness=dto.flavor_profile.sourness,
                bitterness=dto.flavor_profile.bitterness,
                spiciness=dto.flavor_profile.spiciness,
                umami=dto.flavor_profile.umami,
            ),
            skill_level=SkillLevel(dto.skill_level),
            typical_time_available_minutes=dto.typical_time_available_minutes,
            equipment=dto.equipment,
            budget_sensitivity=BudgetSensitivity(dto.budget_sensitivity),
            adventurousness=dto.adventurousness,
        )

        user = await self._repository.get_by_id(dto.user_id)
        if user is None:
            user = User(
                id=dto.user_id,
                hard_constraints=hard_constraints,
                preferences=preferences,
            )
            await self._repository.add(user)
        else:
            user.update_hard_constraints(hard_constraints)
            user.update_preferences(preferences)
            await self._repository.update(user)

        return UserMapper.to_output(user)
