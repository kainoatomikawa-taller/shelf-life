"""TagRawRecipe use case — pipeline stage 2: tag.

Attaches candidate catalog metadata (cuisine/technique/flavor tags) to an
imported raw recipe, queuing it for human review. Tagging is intentionally
just a set of string tags at this stage — resolving raw ingredient text to
catalog Ingredient rows is a separate, later concern (handled by whatever
review tooling prepares the PublishRawRecipeInput).
"""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import RawRecipeOutput, TagRawRecipeInput
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.domain.exceptions import RawRecipeNotFoundError
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository


class TagRawRecipeUseCase:
    """Stage 2 of the ingestion pipeline: tag."""

    def __init__(self, raw_recipe_repository: RawRecipeRepository) -> None:
        self._raw_recipe_repository = raw_recipe_repository

    async def execute(self, dto: TagRawRecipeInput) -> RawRecipeOutput:
        raw_recipe = await self._raw_recipe_repository.get_by_id(dto.raw_recipe_id)
        if raw_recipe is None:
            raise RawRecipeNotFoundError(dto.raw_recipe_id)

        raw_recipe.tag(dto.tags)
        await self._raw_recipe_repository.update(raw_recipe)

        return RawRecipeMapper.to_output(raw_recipe)
