"""ListInventoryItems use case.

Returns all inventory items belonging to a user, with each item's ingredient
resolved so the output can carry a display-friendly ingredient name.
"""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import (
    InventoryItemOutput,
    ListInventoryItemsInput,
)
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.exceptions import IngredientNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository


class ListInventoryItemsUseCase:
    """List all inventory items belonging to a user."""

    def __init__(
        self,
        inventory_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._ingredient_repository = ingredient_repository

    async def execute(
        self, dto: ListInventoryItemsInput
    ) -> list[InventoryItemOutput]:
        items = await self._inventory_repository.list_by_user(dto.user_id)

        outputs = []
        for item in items:
            ingredient = await self._ingredient_repository.get_by_id(
                item.ingredient_id
            )
            if ingredient is None:
                raise IngredientNotFoundError(item.ingredient_id)
            outputs.append(InventoryItemMapper.to_output(item, ingredient))
        return outputs
