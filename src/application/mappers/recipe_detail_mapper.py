"""Mapper between a Recipe (plus its resolved ingredient names) and the
RecipeDetailOutput DTO."""

from __future__ import annotations

from src.application.dtos.recipe_detail_dtos import (
    RecipeDetailOutput,
    RecipeIngredientDetailOutput,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe


class RecipeDetailMapper:
    """Translates a Recipe into the full detail DTO."""

    @staticmethod
    def to_output(
        recipe: Recipe, ingredients_by_id: dict[str, Ingredient]
    ) -> RecipeDetailOutput:
        return RecipeDetailOutput(
            id=recipe.id,
            name=recipe.name,
            time_minutes=recipe.time_minutes,
            difficulty=recipe.difficulty.value,
            cuisine_tags=recipe.cuisine_tags,
            ingredients=[
                RecipeIngredientDetailOutput(
                    ingredient_id=recipe_ingredient.ingredient_id,
                    ingredient_name=RecipeDetailMapper._name_for(
                        recipe_ingredient.ingredient_id, ingredients_by_id
                    ),
                    role=recipe_ingredient.role.value,
                )
                for recipe_ingredient in recipe.ingredients
            ],
            steps=recipe.steps,
        )

    @staticmethod
    def _name_for(ingredient_id: str, ingredients_by_id: dict[str, Ingredient]) -> str:
        ingredient = ingredients_by_id.get(ingredient_id)
        return ingredient.name if ingredient is not None else ingredient_id
