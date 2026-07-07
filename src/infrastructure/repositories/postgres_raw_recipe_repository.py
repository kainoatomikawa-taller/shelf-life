"""PostgreSQL implementation of the RawRecipeRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns for the recipe ingestion staging area.
A raw recipe's tagged ingredients live in a separate join table
(RawRecipeIngredientModel), the same convention as RecipeRepository, so
reads/writes fan out across both tables.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.raw_recipe import RawRecipe
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient
from src.infrastructure.database.models import RawRecipeIngredientModel, RawRecipeModel


class PostgresRawRecipeRepository(RawRecipeRepository):
    """Persists staged raw recipes in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, raw_recipe: RawRecipe) -> None:
        model = RawRecipeModel(id=raw_recipe.id)
        self._apply_to_model(raw_recipe, model)
        self._session.add(model)
        for tagged_ingredient in raw_recipe.tagged_ingredients:
            self._session.add(
                self._to_ingredient_model(raw_recipe.id, tagged_ingredient)
            )
        await self._session.commit()

    async def get_by_id(self, raw_recipe_id: str) -> RawRecipe | None:
        model = await self._session.get(RawRecipeModel, raw_recipe_id)
        if model is None:
            return None
        return await self._to_entity(model)

    async def get_by_source(
        self, source: str, source_recipe_id: str
    ) -> RawRecipe | None:
        result = await self._session.execute(
            select(RawRecipeModel).where(
                RawRecipeModel.source == source,
                RawRecipeModel.source_recipe_id == source_recipe_id,
            )
        )
        model = result.scalars().first()
        return await self._to_entity(model) if model is not None else None

    async def list_by_stage(self, stage: PipelineStage) -> list[RawRecipe]:
        result = await self._session.execute(
            select(RawRecipeModel).where(RawRecipeModel.stage == stage.value)
        )
        return [await self._to_entity(model) for model in result.scalars().all()]

    async def update(self, raw_recipe: RawRecipe) -> None:
        model = await self._session.get(RawRecipeModel, raw_recipe.id)
        if model is None:
            return
        self._apply_to_model(raw_recipe, model)
        await self._session.execute(
            delete(RawRecipeIngredientModel).where(
                RawRecipeIngredientModel.raw_recipe_id == raw_recipe.id
            )
        )
        for tagged_ingredient in raw_recipe.tagged_ingredients:
            self._session.add(
                self._to_ingredient_model(raw_recipe.id, tagged_ingredient)
            )
        await self._session.commit()

    async def delete(self, raw_recipe_id: str) -> None:
        await self._session.execute(
            delete(RawRecipeModel).where(RawRecipeModel.id == raw_recipe_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @staticmethod
    def _apply_to_model(raw_recipe: RawRecipe, model: RawRecipeModel) -> None:
        model.source = raw_recipe.source
        model.source_recipe_id = raw_recipe.source_recipe_id
        model.license = raw_recipe.license
        model.raw_name = raw_recipe.raw_name
        model.raw_ingredients = list(raw_recipe.raw_ingredients)
        model.raw_method = list(raw_recipe.raw_method)
        model.raw_attribution = raw_recipe.raw_attribution
        model.imported_at = raw_recipe.imported_at
        model.stage = raw_recipe.stage.value
        model.cuisine_tags = list(raw_recipe.cuisine_tags)
        model.flavor_tags = list(raw_recipe.flavor_tags)
        model.technique_tags = list(raw_recipe.technique_tags)
        model.difficulty = (
            raw_recipe.difficulty.value if raw_recipe.difficulty else None
        )
        model.time_minutes = raw_recipe.time_minutes
        model.review_notes = raw_recipe.review_notes
        model.rejected_reason = raw_recipe.rejected_reason
        model.published_recipe_id = raw_recipe.published_recipe_id

    @staticmethod
    def _to_ingredient_model(
        raw_recipe_id: str, tagged_ingredient: TaggedIngredient
    ) -> RawRecipeIngredientModel:
        return RawRecipeIngredientModel(
            id=str(uuid.uuid4()),
            raw_recipe_id=raw_recipe_id,
            raw_text=tagged_ingredient.raw_text,
            ingredient_id=tagged_ingredient.ingredient_id,
            role=tagged_ingredient.role.value,
        )

    async def _to_entity(self, model: RawRecipeModel) -> RawRecipe:
        result = await self._session.execute(
            select(RawRecipeIngredientModel).where(
                RawRecipeIngredientModel.raw_recipe_id == model.id
            )
        )
        tagged_ingredients = [
            TaggedIngredient(
                raw_text=row.raw_text,
                ingredient_id=row.ingredient_id,
                role=IngredientRole(row.role),
            )
            for row in result.scalars().all()
        ]
        return RawRecipe(
            id=model.id,
            source=model.source,
            source_recipe_id=model.source_recipe_id,
            license=model.license,
            raw_name=model.raw_name,
            raw_ingredients=list(model.raw_ingredients),
            raw_method=list(model.raw_method),
            imported_at=model.imported_at,
            raw_attribution=model.raw_attribution,
            stage=PipelineStage(model.stage),
            cuisine_tags=list(model.cuisine_tags),
            flavor_tags=list(model.flavor_tags),
            technique_tags=list(model.technique_tags),
            difficulty=SkillLevel(model.difficulty) if model.difficulty else None,
            time_minutes=model.time_minutes,
            tagged_ingredients=tagged_ingredients,
            review_notes=model.review_notes,
            rejected_reason=model.rejected_reason,
            published_recipe_id=model.published_recipe_id,
        )
