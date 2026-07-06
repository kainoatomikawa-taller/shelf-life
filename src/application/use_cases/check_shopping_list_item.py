"""CheckShoppingListItem use case (§5.7 AC2).

Backs the check-off-as-you-shop interaction on the Shopping List tab.
"""

from __future__ import annotations

from src.application.dtos.shopping_list_dtos import (
    CheckShoppingListItemInput,
    ShoppingListEntryOutput,
)
from src.application.mappers.shopping_list_item_mapper import ShoppingListItemMapper
from src.domain.exceptions import (
    IngredientNotFoundError,
    ShoppingListItemNotFoundError,
)
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)


class CheckShoppingListItemUseCase:
    """Toggle a shopping list item's checked state."""

    def __init__(
        self,
        shopping_list_item_repository: ShoppingListItemRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._shopping_list_item_repository = shopping_list_item_repository
        self._ingredient_repository = ingredient_repository

    async def execute(
        self, dto: CheckShoppingListItemInput
    ) -> ShoppingListEntryOutput:
        item = await self._shopping_list_item_repository.get_by_id(dto.item_id)
        if item is None:
            raise ShoppingListItemNotFoundError(dto.item_id)

        if dto.checked:
            item.mark_checked()
        else:
            item.mark_unchecked()
        await self._shopping_list_item_repository.update(item)

        ingredient = await self._ingredient_repository.get_by_id(item.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(item.ingredient_id)

        return ShoppingListItemMapper.to_output(item, ingredient)
