"""Mapper between the InventoryItem entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import InventoryItemOutput
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem


class InventoryItemMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(item: InventoryItem, ingredient: Ingredient) -> InventoryItemOutput:
        return InventoryItemOutput(
            id=item.id,
            user_id=item.user_id,
            ingredient_id=item.ingredient_id,
            ingredient_name=ingredient.name,
            quantity_state=item.quantity_state.value,
            storage_location=item.storage_location.value,
            purchase_date=item.purchase_date,
            printed_package_date=item.printed_package_date,
            is_frozen=item.is_frozen,
            computed_freshness_date=item.computed_freshness_date,
            freshness_date_type=item.freshness_date_type.value,
            freshness_status=item.freshness_status.value,
            added_at=item.added_at,
            notes=item.notes,
        )
