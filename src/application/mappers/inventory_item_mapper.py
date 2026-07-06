"""Mapper between the InventoryItem entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.inventory_item_dtos import (
    InventoryItemOutput,
    SpoilageCheckTipOutput,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.services.freshness_presenter import FreshnessPresenter


class InventoryItemMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(
        item: InventoryItem,
        ingredient: Ingredient,
        presenter: FreshnessPresenter | None = None,
    ) -> InventoryItemOutput:
        display = (presenter or FreshnessPresenter()).present(
            item.freshness_date_type, item.freshness_status, ingredient.category
        )
        spoilage_check_tip = (
            SpoilageCheckTipOutput(
                smell=display.spoilage_check_tip.smell,
                look=display.spoilage_check_tip.look,
                texture=display.spoilage_check_tip.texture,
            )
            if display.spoilage_check_tip is not None
            else None
        )
        return InventoryItemOutput(
            id=item.id,
            user_id=item.user_id,
            ingredient_id=item.ingredient_id,
            ingredient_name=ingredient.name,
            ingredient_category=ingredient.category.value,
            quantity_state=item.quantity_state.value,
            storage_location=item.storage_location.value,
            purchase_date=item.purchase_date,
            printed_package_date=item.printed_package_date,
            is_frozen=item.is_frozen,
            computed_freshness_date=item.computed_freshness_date,
            freshness_date_type=item.freshness_date_type.value,
            freshness_date_label=display.date_label.label,
            freshness_date_tooltip=display.date_label.tooltip,
            freshness_status=item.freshness_status.value,
            spoilage_check_tip=spoilage_check_tip,
            added_at=item.added_at,
            notes=item.notes,
        )
