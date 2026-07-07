"""In-memory RawRecipeRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.raw_recipe import RawRecipe
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.value_objects.pipeline_stage import PipelineStage


class InMemoryRawRecipeRepository(RawRecipeRepository):
    def __init__(self, raw_recipes: list[RawRecipe] | None = None) -> None:
        self._raw_recipes: dict[str, RawRecipe] = {
            r.id: r for r in (raw_recipes or [])
        }

    async def add(self, raw_recipe: RawRecipe) -> None:
        self._raw_recipes[raw_recipe.id] = raw_recipe

    async def get_by_id(self, raw_recipe_id: str) -> RawRecipe | None:
        return self._raw_recipes.get(raw_recipe_id)

    async def get_by_source(
        self, source: str, source_recipe_id: str
    ) -> RawRecipe | None:
        for raw_recipe in self._raw_recipes.values():
            if (
                raw_recipe.source == source
                and raw_recipe.source_recipe_id == source_recipe_id
            ):
                return raw_recipe
        return None

    async def list_by_stage(self, stage: PipelineStage) -> list[RawRecipe]:
        return [r for r in self._raw_recipes.values() if r.stage is stage]

    async def update(self, raw_recipe: RawRecipe) -> None:
        self._raw_recipes[raw_recipe.id] = raw_recipe

    async def delete(self, raw_recipe_id: str) -> None:
        self._raw_recipes.pop(raw_recipe_id, None)
