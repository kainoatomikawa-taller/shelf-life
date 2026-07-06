"""Mapper between the User entity and its DTOs."""

from __future__ import annotations

from dataclasses import asdict

from src.application.dtos.user_dtos import UserProfileOutput
from src.domain.entities.user import User


class UserMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(user: User) -> UserProfileOutput:
        preferences = user.preferences
        return UserProfileOutput(
            id=user.id,
            allergies=user.hard_constraints.allergies,
            diet_type=user.hard_constraints.diet_type.value,
            disliked_ingredients=preferences.disliked_ingredients,
            liked_cuisines=preferences.liked_cuisines,
            flavor_profile=asdict(preferences.flavor_profile),
            skill_level=preferences.skill_level.value,
            typical_time_available_minutes=preferences.typical_time_available_minutes,
            equipment=preferences.equipment,
            budget_sensitivity=preferences.budget_sensitivity.value,
            adventurousness=preferences.adventurousness,
            taste_vector=user.taste_vector.as_dict(),
        )
