"""Mapper between the Ingredient entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.ingredient_dtos import IngredientSummaryOutput
from src.domain.entities.ingredient import Ingredient


class IngredientMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_summary(ingredient: Ingredient) -> IngredientSummaryOutput:
        return IngredientSummaryOutput(
            id=ingredient.id,
            name=ingredient.name,
            aliases=tuple(ingredient.aliases),
            category=ingredient.category.value,
            default_storage_location=ingredient.default_storage_location.value,
        )
