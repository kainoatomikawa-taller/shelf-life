"""PostgreSQL implementation of the RecipeRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns. A recipe's ingredient list lives in a
separate join table (RecipeIngredientModel) rather than an array column, so
reads/writes fan out across both tables.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.recipe import Recipe
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel
from src.infrastructure.database.models import RecipeIngredientModel, RecipeModel


class PostgresRecipeRepository(RecipeRepository):
    """Persists catalog recipes in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, recipe: Recipe) -> None:
        model = RecipeModel(id=recipe.id)
        self._apply_to_model(recipe, model)
        self._session.add(model)
        for recipe_ingredient in recipe.ingredients:
            self._session.add(
                self._to_ingredient_model(recipe.id, recipe_ingredient)
            )
        await self._session.commit()

    async def get_by_id(self, recipe_id: str) -> Recipe | None:
        model = await self._session.get(RecipeModel, recipe_id)
        if model is None:
            return None
        return await self._to_entity(model)

    async def list_all(self) -> list[Recipe]:
        result = await self._session.execute(select(RecipeModel))
        return [await self._to_entity(model) for model in result.scalars().all()]

    async def list_by_ingredient(self, ingredient_id: str) -> list[Recipe]:
        result = await self._session.execute(
            select(RecipeModel)
            .join(
                RecipeIngredientModel,
                RecipeIngredientModel.recipe_id == RecipeModel.id,
            )
            .where(RecipeIngredientModel.ingredient_id == ingredient_id)
        )
        return [await self._to_entity(model) for model in result.scalars().all()]

    async def update(self, recipe: Recipe) -> None:
        model = await self._session.get(RecipeModel, recipe.id)
        if model is None:
            return
        self._apply_to_model(recipe, model)
        await self._session.execute(
            delete(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_id == recipe.id
            )
        )
        for recipe_ingredient in recipe.ingredients:
            self._session.add(
                self._to_ingredient_model(recipe.id, recipe_ingredient)
            )
        await self._session.commit()

    async def delete(self, recipe_id: str) -> None:
        await self._session.execute(
            delete(RecipeModel).where(RecipeModel.id == recipe_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @staticmethod
    def _apply_to_model(recipe: Recipe, model: RecipeModel) -> None:
        flavor_profile = recipe.flavor_profile
        model.name = recipe.name
        model.cuisine_tags = list(recipe.cuisine_tags)
        model.flavor_tags = list(recipe.flavor_tags)
        model.technique_tags = list(recipe.technique_tags)
        model.equipment_needed = list(recipe.equipment_needed)
        model.steps = list(recipe.steps)
        model.time_minutes = recipe.time_minutes
        model.difficulty = recipe.difficulty.value
        model.popularity_score = recipe.popularity_score
        model.flavor_profile_sweetness = flavor_profile.sweetness
        model.flavor_profile_saltiness = flavor_profile.saltiness
        model.flavor_profile_sourness = flavor_profile.sourness
        model.flavor_profile_bitterness = flavor_profile.bitterness
        model.flavor_profile_spiciness = flavor_profile.spiciness
        model.flavor_profile_umami = flavor_profile.umami

    @staticmethod
    def _to_ingredient_model(
        recipe_id: str, recipe_ingredient: RecipeIngredient
    ) -> RecipeIngredientModel:
        return RecipeIngredientModel(
            id=f"{recipe_id}:{recipe_ingredient.ingredient_id}",
            recipe_id=recipe_id,
            ingredient_id=recipe_ingredient.ingredient_id,
            role=recipe_ingredient.role.value,
        )

    async def _to_entity(self, model: RecipeModel) -> Recipe:
        result = await self._session.execute(
            select(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_id == model.id
            )
        )
        ingredients = [
            RecipeIngredient(
                ingredient_id=row.ingredient_id, role=IngredientRole(row.role)
            )
            for row in result.scalars().all()
        ]
        return Recipe(
            id=model.id,
            name=model.name,
            ingredients=ingredients,
            steps=list(model.steps),
            time_minutes=model.time_minutes,
            difficulty=SkillLevel(model.difficulty),
            cuisine_tags=list(model.cuisine_tags),
            flavor_tags=list(model.flavor_tags),
            technique_tags=list(model.technique_tags),
            equipment_needed=list(model.equipment_needed),
            popularity_score=model.popularity_score,
            flavor_profile=FlavorProfile(
                sweetness=model.flavor_profile_sweetness,
                saltiness=model.flavor_profile_saltiness,
                sourness=model.flavor_profile_sourness,
                bitterness=model.flavor_profile_bitterness,
                spiciness=model.flavor_profile_spiciness,
                umami=model.flavor_profile_umami,
            ),
        )
