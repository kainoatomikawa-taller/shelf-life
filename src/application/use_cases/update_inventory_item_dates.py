"""UpdateInventoryItemDates use case.

Backs the "edit dates" quick action on the Kitchen list (§5.2): corrects the
purchase and/or printed package date and recomputes the labeled freshness
date to match.
"""

from __future__ import annotations

from datetime import date

from src.application.dtos.inventory_item_dtos import (
    InventoryItemOutput,
    UpdateInventoryItemDatesInput,
)
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.exceptions import IngredientNotFoundError, InventoryItemNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository


class UpdateInventoryItemDatesUseCase:
    """Correct an inventory item's purchase/package dates."""

    def __init__(
        self,
        inventory_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._ingredient_repository = ingredient_repository

    async def execute(
        self, dto: UpdateInventoryItemDatesInput
    ) -> InventoryItemOutput:
        item = await self._inventory_repository.get_by_id(dto.item_id)
        if item is None:
            raise InventoryItemNotFoundError(dto.item_id)

        ingredient = await self._ingredient_repository.get_by_id(item.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(item.ingredient_id)

        item.update_dates(
            ingredient,
            today=date.today(),
            purchase_date=dto.purchase_date,
            printed_package_date=dto.printed_package_date,
        )
        await self._inventory_repository.update(item)
        return InventoryItemMapper.to_output(item, ingredient)
