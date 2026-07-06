"""Mapper between a Recipe (plus its computed progress) and the
DiscoverRecipeCardOutput DTO for the Discover feed (§5.4)."""

from __future__ import annotations

from src.application.dtos.discover_dtos import DiscoverRecipeCardOutput
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.recipe_ingredient_progress import (
    RecipeIngredientProgress,
)


class DiscoverRecipeCardMapper:
    """Translates a Recipe and its precomputed progress into a card DTO."""

    @staticmethod
    def to_output(
        recipe: Recipe, progress: RecipeIngredientProgress
    ) -> DiscoverRecipeCardOutput:
        return DiscoverRecipeCardOutput(
            id=recipe.id,
            name=recipe.name,
            time_minutes=recipe.time_minutes,
            difficulty=recipe.difficulty.value,
            cuisine_tags=recipe.cuisine_tags,
            have_count=progress.have_count,
            total_count=progress.total_count,
        )
