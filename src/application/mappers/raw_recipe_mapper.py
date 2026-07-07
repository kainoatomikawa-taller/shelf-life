"""Mapper between the RawRecipe entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import RawRecipeOutput, TaggedIngredientOutput
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
            cuisine_tags=raw_recipe.cuisine_tags,
            flavor_tags=raw_recipe.flavor_tags,
            technique_tags=raw_recipe.technique_tags,
            difficulty=raw_recipe.difficulty.value if raw_recipe.difficulty else None,
            time_minutes=raw_recipe.time_minutes,
            tagged_ingredients=[
                TaggedIngredientOutput(
                    raw_text=i.raw_text,
                    ingredient_id=i.ingredient_id,
                    role=i.role.value,
                    matched=i.is_matched,
                )
                for i in raw_recipe.tagged_ingredients
            ],
            raw_attribution=raw_recipe.raw_attribution,
            review_notes=raw_recipe.review_notes,
            rejected_reason=raw_recipe.rejected_reason,
            published_recipe_id=raw_recipe.published_recipe_id,
        )
