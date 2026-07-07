"""Mapper between the RawRecipe entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import RawRecipeOutput
from src.domain.entities.raw_recipe import RawRecipe


class RawRecipeMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(raw_recipe: RawRecipe) -> RawRecipeOutput:
        return RawRecipeOutput(
            id=raw_recipe.id,
            source=raw_recipe.source,
            source_recipe_id=raw_recipe.source_recipe_id,
            license=raw_recipe.license,
            raw_name=raw_recipe.raw_name,
            raw_ingredients=raw_recipe.raw_ingredients,
            raw_method=raw_recipe.raw_method,
            stage=raw_recipe.stage.value,
            tags=raw_recipe.tags,
            raw_attribution=raw_recipe.raw_attribution,
            review_notes=raw_recipe.review_notes,
            rejected_reason=raw_recipe.rejected_reason,
            published_recipe_id=raw_recipe.published_recipe_id,
        )
