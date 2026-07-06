"""AddInventoryItem use case.

Creates a new inventory item from the add-item screen (§5.2). Only the
ingredient is required — storage location and quantity state fall back to
smart defaults derived from the chosen ingredient's catalog entry when
skipped, and purchase/package dates are left for the freshness engine to
estimate around.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from src.application.dtos.inventory_item_dtos import (
    AddInventoryItemInput,
    InventoryItemOutput,
)
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.entities.inventory_item import InventoryItem
from src.domain.exceptions import IngredientNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.storage_location import StorageLocation


class AddInventoryItemUseCase:
    """Add a new item to a user's inventory, applying category defaults."""

    def __init__(
        self,
        inventory_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._ingredient_repository = ingredient_repository

    async def execute(self, dto: AddInventoryItemInput) -> InventoryItemOutput:
        ingredient = await self._ingredient_repository.get_by_id(dto.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(dto.ingredient_id)

        quantity_state = (
            QuantityState(dto.quantity_state)
            if dto.quantity_state is not None
            else QuantityState.IN
        )
        storage_location = (
            StorageLocation(dto.storage_location)
            if dto.storage_location is not None
            else ingredient.default_storage_location
        )

        item = InventoryItem.create(
            id=str(uuid.uuid4()),
            user_id=dto.user_id,
            ingredient=ingredient,
            quantity_state=quantity_state,
            storage_location=storage_location,
            added_at=datetime.now(UTC),
            today=date.today(),
            purchase_date=dto.purchase_date,
            printed_package_date=dto.printed_package_date,
            is_frozen=dto.is_frozen,
            notes=dto.notes,
        )
        await self._inventory_repository.add(item)
        return InventoryItemMapper.to_output(item, ingredient)
