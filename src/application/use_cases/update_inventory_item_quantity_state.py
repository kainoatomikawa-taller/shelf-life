"""UpdateInventoryItemQuantityState use case.

Backs the one-tap Mark Low / Mark Out (and undo, Mark In) quick actions on
the Kitchen list (§5.2 AC2).
"""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import (
    InventoryItemOutput,
    UpdateQuantityStateInput,
)
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.exceptions import IngredientNotFoundError, InventoryItemNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.value_objects.quantity_state import QuantityState


class UpdateInventoryItemQuantityStateUseCase:
    """Update an inventory item's coarse quantity state."""

    def __init__(
        self,
        inventory_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._ingredient_repository = ingredient_repository

    async def execute(self, dto: UpdateQuantityStateInput) -> InventoryItemOutput:
        item = await self._inventory_repository.get_by_id(dto.item_id)
        if item is None:
            raise InventoryItemNotFoundError(dto.item_id)

        ingredient = await self._ingredient_repository.get_by_id(item.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(item.ingredient_id)

        item.update_quantity_state(QuantityState(dto.quantity_state))
        await self._inventory_repository.update(item)
        return InventoryItemMapper.to_output(item, ingredient)
