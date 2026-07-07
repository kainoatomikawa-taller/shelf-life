"""GetRecipeDetail use case: the full ingredient list and procedure behind
a recipe, shown when a user taps into a Discover or Cook Now card."""

from __future__ import annotations

from src.application.dtos.recipe_detail_dtos import (
    GetRecipeDetailInput,
    RecipeDetailOutput,
)
from src.application.mappers.recipe_detail_mapper import RecipeDetailMapper
from src.domain.entities.ingredient import Ingredient
from src.domain.exceptions import RecipeNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.recipe_repository import RecipeRepository


class GetRecipeDetailUseCase:
    """Assemble the full detail view for a single recipe."""

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._ingredient_repository = ingredient_repository

    async def execute(self, dto: GetRecipeDetailInput) -> RecipeDetailOutput:
        recipe = await self._recipe_repository.get_by_id(dto.recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(dto.recipe_id)

        ingredients_by_id: dict[str, Ingredient] = {}
        for recipe_ingredient in recipe.ingredients:
            ingredient = await self._ingredient_repository.get_by_id(
                recipe_ingredient.ingredient_id
            )
            if ingredient is not None:
                ingredients_by_id[recipe_ingredient.ingredient_id] = ingredient

        return RecipeDetailMapper.to_output(recipe, ingredients_by_id)
