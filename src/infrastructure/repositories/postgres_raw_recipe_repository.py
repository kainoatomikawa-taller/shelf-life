"""PostgreSQL implementation of the RawRecipeRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns for the recipe ingestion staging area.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.raw_recipe import RawRecipe
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.infrastructure.database.models import RawRecipeModel


class PostgresRawRecipeRepository(RawRecipeRepository):
    """Persists staged raw recipes in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, raw_recipe: RawRecipe) -> None:
        model = RawRecipeModel(id=raw_recipe.id)
        self._apply_to_model(raw_recipe, model)
        self._session.add(model)
        await self._session.commit()

    async def get_by_id(self, raw_recipe_id: str) -> RawRecipe | None:
        model = await self._session.get(RawRecipeModel, raw_recipe_id)
        if model is None:
            return None
        return self._to_entity(model)

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
        return self._to_entity(model) if model is not None else None

    async def list_by_stage(self, stage: PipelineStage) -> list[RawRecipe]:
        result = await self._session.execute(
            select(RawRecipeModel).where(RawRecipeModel.stage == stage.value)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, raw_recipe: RawRecipe) -> None:
        model = await self._session.get(RawRecipeModel, raw_recipe.id)
        if model is None:
            return
        self._apply_to_model(raw_recipe, model)
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
        model.tags = list(raw_recipe.tags)
        model.review_notes = raw_recipe.review_notes
        model.rejected_reason = raw_recipe.rejected_reason
        model.published_recipe_id = raw_recipe.published_recipe_id

    @staticmethod
    def _to_entity(model: RawRecipeModel) -> RawRecipe:
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
            tags=list(model.tags),
            review_notes=model.review_notes,
            rejected_reason=model.rejected_reason,
            published_recipe_id=model.published_recipe_id,
        )
