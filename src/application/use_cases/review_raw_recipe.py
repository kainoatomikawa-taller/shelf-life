"""ReviewRawRecipe use case — pipeline stage 3: review.

A human reviewer's verdict on a tagged raw recipe: approve it (clearing the
way to publish) or reject it outright, with a required reason. Rejection is
terminal — a rejected raw recipe is never published.
"""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import RawRecipeOutput, ReviewRawRecipeInput
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.domain.exceptions import RawRecipeNotFoundError, ValidationError
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository


class ReviewRawRecipeUseCase:
    """Stage 3 of the ingestion pipeline: review."""

    def __init__(self, raw_recipe_repository: RawRecipeRepository) -> None:
        self._raw_recipe_repository = raw_recipe_repository

    async def execute(self, dto: ReviewRawRecipeInput) -> RawRecipeOutput:
        raw_recipe = await self._raw_recipe_repository.get_by_id(dto.raw_recipe_id)
        if raw_recipe is None:
            raise RawRecipeNotFoundError(dto.raw_recipe_id)

        if dto.approve:
            raw_recipe.approve(review_notes=dto.notes)
        else:
            if not dto.notes:
                raise ValidationError("A rejection reason is required.")
            raw_recipe.reject(dto.notes)

        await self._raw_recipe_repository.update(raw_recipe)

        return RawRecipeMapper.to_output(raw_recipe)
