"""GenerateShoppingListForRecipe use case (§5.4).

The "tap a recipe" half of the Discover screen's shopping list flow:
computes only a recipe's true gaps (ShoppingListGenerator, via
shopping_list_support.compute_true_gaps) for the requesting user (AC3)
without persisting anything, so the client can show a preview before the
one-tap "add" (AddShoppingListItemsUseCase) commits it. Any essential
ingredient the user's substitution options already cover is deliberately
left off — it isn't something the cook needs to buy.
"""

from __future__ import annotations

from src.application.dtos.discover_dtos import (
    GenerateShoppingListInput,
    ShoppingListItemOutput,
    ShoppingListOutput,
)
from src.application.use_cases.shopping_list_support import compute_true_gaps
from src.domain.exceptions import RecipeNotFoundError, UserNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.shopping_list_generator import ShoppingListGenerator


class GenerateShoppingListForRecipeUseCase:
    """Compute a recipe's true ingredient gaps for a user, without persisting."""

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        substitution_repository: SubstitutionRepository,
        ingredient_repository: IngredientRepository,
        inventory_item_repository: InventoryItemRepository,
        user_repository: UserRepository,
        shopping_list_generator: ShoppingListGenerator | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._substitution_repository = substitution_repository
        self._ingredient_repository = ingredient_repository
        self._inventory_item_repository = inventory_item_repository
        self._user_repository = user_repository
        self._shopping_list_generator = (
            shopping_list_generator or ShoppingListGenerator()
        )

    async def execute(self, dto: GenerateShoppingListInput) -> ShoppingListOutput:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        recipe = await self._recipe_repository.get_by_id(dto.recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(dto.recipe_id)

        gap_ingredient_ids, ingredients_by_id = await compute_true_gaps(
            recipe,
            user,
            dto.user_id,
            self._inventory_item_repository,
            self._substitution_repository,
            self._ingredient_repository,
            self._shopping_list_generator,
        )

        return ShoppingListOutput(
            recipe_id=recipe.id,
            items=[
                ShoppingListItemOutput(
                    ingredient_id=ingredient_id,
                    ingredient_name=ingredients_by_id[ingredient_id].name,
                )
                for ingredient_id in gap_ingredient_ids
            ],
        )
