"""Mapper between a Recipe (plus its computed badge data) and the
RecipeCardOutput DTO for the Cook Now feed (§5.3)."""

from __future__ import annotations

from src.application.dtos.cook_now_dtos import (
    RecipeBadgesOutput,
    RecipeCardOutput,
    SubstitutionSuggestionOutput,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.substitution_suggestion import SubstitutionSuggestion


class RecipeCardMapper:
    """Translates a Recipe and its precomputed badge inputs into a card DTO."""

    @staticmethod
    def to_output(
        recipe: Recipe,
        expiring_ingredient: Ingredient | None,
        low_stock_ingredient: Ingredient | None,
        substitutions: list[tuple[str, SubstitutionSuggestion]],
        ingredients_by_id: dict[str, Ingredient],
    ) -> RecipeCardOutput:
        """`substitutions` pairs each swapped-out essential ingredient id
        with the suggestion chosen to replace it.
        """
        badges = RecipeBadgesOutput(
            expiring_ingredient_name=(
                expiring_ingredient.name if expiring_ingredient else None
            ),
            low_stock_ingredient_name=(
                low_stock_ingredient.name if low_stock_ingredient else None
            ),
            substitution_count=len(substitutions),
        )
        return RecipeCardOutput(
            id=recipe.id,
            name=recipe.name,
            time_minutes=recipe.time_minutes,
            difficulty=recipe.difficulty.value,
            cuisine_tags=recipe.cuisine_tags,
            badges=badges,
            substitutions=[
                SubstitutionSuggestionOutput(
                    from_ingredient_id=from_ingredient_id,
                    from_ingredient_name=ingredients_by_id[from_ingredient_id].name,
                    to_ingredient_id=suggestion.to_ingredient_id,
                    to_ingredient_name=ingredients_by_id[
                        suggestion.to_ingredient_id
                    ].name,
                    disclosure=suggestion.disclosure,
                    ratio_note=suggestion.substitution.ratio_note,
                    confidence=suggestion.confidence,
                )
                for from_ingredient_id, suggestion in substitutions
            ],
        )
