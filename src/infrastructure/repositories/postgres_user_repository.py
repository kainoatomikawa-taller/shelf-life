"""PostgreSQL implementation of the UserRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns, flattening/unflattening the
FlavorProfile and TasteVector value objects into scalar/array columns.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.budget_sensitivity import BudgetSensitivity
from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.taste_vector import TasteVector
from src.infrastructure.database.models import UserModel


class PostgresUserRepository(UserRepository):
    """Persists users in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        self._session.add(self._to_model(user))
        await self._session.commit()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            return
        self._apply_to_model(user, model)
        await self._session.commit()

    async def delete(self, user_id: str) -> None:
        await self._session.execute(delete(UserModel).where(UserModel.id == user_id))
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @classmethod
    def _to_model(cls, user: User) -> UserModel:
        model = UserModel(id=user.id)
        cls._apply_to_model(user, model)
        return model

    @staticmethod
    def _apply_to_model(user: User, model: UserModel) -> None:
        hard_constraints = user.hard_constraints
        preferences = user.preferences
        flavor_profile = preferences.flavor_profile
        taste_vector = user.taste_vector.as_dict()

        model.allergies = list(hard_constraints.allergies)
        model.diet_type = hard_constraints.diet_type.value

        model.disliked_ingredients = list(preferences.disliked_ingredients)
        model.liked_cuisines = list(preferences.liked_cuisines)

        model.flavor_profile_sweetness = flavor_profile.sweetness
        model.flavor_profile_saltiness = flavor_profile.saltiness
        model.flavor_profile_sourness = flavor_profile.sourness
        model.flavor_profile_bitterness = flavor_profile.bitterness
        model.flavor_profile_spiciness = flavor_profile.spiciness
        model.flavor_profile_umami = flavor_profile.umami

        model.skill_level = preferences.skill_level.value
        model.typical_time_available_minutes = (
            preferences.typical_time_available_minutes
        )
        model.equipment = list(preferences.equipment)
        model.budget_sensitivity = preferences.budget_sensitivity.value
        model.adventurousness = preferences.adventurousness

        model.taste_vector = [
            taste_vector["sweetness"],
            taste_vector["saltiness"],
            taste_vector["sourness"],
            taste_vector["bitterness"],
            taste_vector["spiciness"],
            taste_vector["umami"],
        ]

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        hard_constraints = HardConstraints(
            allergies=tuple(model.allergies),
            diet_type=DietType(model.diet_type),
        )
        preferences = SoftPreferences(
            disliked_ingredients=tuple(model.disliked_ingredients),
            liked_cuisines=tuple(model.liked_cuisines),
            flavor_profile=FlavorProfile(
                sweetness=model.flavor_profile_sweetness,
                saltiness=model.flavor_profile_saltiness,
                sourness=model.flavor_profile_sourness,
                bitterness=model.flavor_profile_bitterness,
                spiciness=model.flavor_profile_spiciness,
                umami=model.flavor_profile_umami,
            ),
            skill_level=SkillLevel(model.skill_level),
            typical_time_available_minutes=model.typical_time_available_minutes,
            equipment=tuple(model.equipment),
            budget_sensitivity=BudgetSensitivity(model.budget_sensitivity),
            adventurousness=model.adventurousness,
        )
        taste_vector = TasteVector(weights=tuple(model.taste_vector))
        return User(
            id=model.id,
            hard_constraints=hard_constraints,
            preferences=preferences,
            taste_vector=taste_vector,
        )
