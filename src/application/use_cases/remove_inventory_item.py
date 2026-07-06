"""RemoveInventoryItem use case.

Backs the "used it up" and "delete" quick actions on the Kitchen list
(§5.2): both remove the item outright once it's no longer worth tracking.
"""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import RemoveInventoryItemInput
from src.domain.exceptions import InventoryItemNotFoundError
from src.domain.repositories.inventory_item_repository import InventoryItemRepository


class RemoveInventoryItemUseCase:
    """Remove an inventory item."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self._repository = repository

    async def execute(self, dto: RemoveInventoryItemInput) -> None:
        item = await self._repository.get_by_id(dto.item_id)
        if item is None:
            raise InventoryItemNotFoundError(dto.item_id)
        await self._repository.delete(dto.item_id)
