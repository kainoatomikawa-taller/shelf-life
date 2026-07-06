"""AddShoppingListItems use case (§5.4).

The one-tap "add" behind a Discover recipe's shopping list (AC3):
recomputes the recipe's true gaps server-side — via the same
shopping_list_support.compute_true_gaps helper GenerateShoppingListForRecipeUseCase
previews with, rather than trusting a client-supplied ingredient list —
and persists one ShoppingListItem per gap still true to the user's current
inventory. Recomputing also makes the action idempotent to retry: tapping
"add" again after browsing away and back only ever adds gaps that are
still real and not already on the list.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.application.dtos.discover_dtos import (
    AddShoppingListItemsInput,
    ShoppingListItemOutput,
    ShoppingListOutput,
)
from src.application.use_cases.shopping_list_support import compute_true_gaps
from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.exceptions import RecipeNotFoundError, UserNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.shopping_list_generator import ShoppingListGenerator


class AddShoppingListItemsUseCase:
    """Regenerate a recipe's true gaps and persist them to the user's
    shopping list in one action.
    """

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        substitution_repository: SubstitutionRepository,
        ingredient_repository: IngredientRepository,
        inventory_item_repository: InventoryItemRepository,
        user_repository: UserRepository,
        shopping_list_item_repository: ShoppingListItemRepository,
        shopping_list_generator: ShoppingListGenerator | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._substitution_repository = substitution_repository
        self._ingredient_repository = ingredient_repository
        self._inventory_item_repository = inventory_item_repository
        self._user_repository = user_repository
        self._shopping_list_item_repository = shopping_list_item_repository
        self._shopping_list_generator = (
            shopping_list_generator or ShoppingListGenerator()
        )

    async def execute(self, dto: AddShoppingListItemsInput) -> ShoppingListOutput:
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

        existing_items = await self._shopping_list_item_repository.list_by_user(
            dto.user_id
        )
        already_listed_ingredient_ids = {i.ingredient_id for i in existing_items}

        added: list[ShoppingListItemOutput] = []
        now = datetime.now(UTC)
        for ingredient_id in gap_ingredient_ids:
            if ingredient_id in already_listed_ingredient_ids:
                continue
            item = ShoppingListItem(
                id=str(uuid.uuid4()),
                user_id=dto.user_id,
                ingredient_id=ingredient_id,
                source_recipe_ids=[recipe.id],
                added_at=now,
            )
            await self._shopping_list_item_repository.add(item)
            added.append(
                ShoppingListItemOutput(
                    ingredient_id=ingredient_id,
                    ingredient_name=ingredients_by_id[ingredient_id].name,
                )
            )

        return ShoppingListOutput(recipe_id=recipe.id, items=added)
