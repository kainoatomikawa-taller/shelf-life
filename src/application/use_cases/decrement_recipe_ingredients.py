"""DecrementRecipeIngredients use case (§5.6 AC3).

Applies the pantry stock decrement the post-cook rating prompt offered
(SubmitRatingUseCase) but never applied on its own: steps every eligible
inventory item for the recipe one notch down the in -> low -> out ladder.
Only runs when the user explicitly opts in — there is no path that reaches
this use case without a separate, deliberate call.
"""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import InventoryItemOutput
from src.application.dtos.rating_dtos import DecrementRecipeIngredientsInput
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.exceptions import (
    IngredientNotFoundError,
    RecipeNotFoundError,
    UserNotFoundError,
)
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.recipe_stock_decrementer import RecipeStockDecrementer


class DecrementRecipeIngredientsUseCase:
    """Step down the quantity state of every inventory item eligible for
    this recipe's optional stock decrement."""

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        inventory_item_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
        user_repository: UserRepository,
        stock_decrementer: RecipeStockDecrementer | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._inventory_item_repository = inventory_item_repository
        self._ingredient_repository = ingredient_repository
        self._user_repository = user_repository
        self._stock_decrementer = stock_decrementer or RecipeStockDecrementer()

    async def execute(
        self, dto: DecrementRecipeIngredientsInput
    ) -> list[InventoryItemOutput]:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        recipe = await self._recipe_repository.get_by_id(dto.recipe_id)
        if recipe is None:
            raise RecipeNotFoundError(dto.recipe_id)

        inventory_items = await self._inventory_item_repository.list_by_user(
            dto.user_id
        )
        decrementable_items = self._stock_decrementer.find_decrementable_items(
            recipe, inventory_items
        )

        outputs: list[InventoryItemOutput] = []
        for item in decrementable_items:
            item.update_quantity_state(item.quantity_state.step_down())
            await self._inventory_item_repository.update(item)

            ingredient = await self._ingredient_repository.get_by_id(
                item.ingredient_id
            )
            if ingredient is None:
                raise IngredientNotFoundError(item.ingredient_id)
            outputs.append(InventoryItemMapper.to_output(item, ingredient))

        return outputs
