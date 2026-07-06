"""Mapper between the ShoppingListItem entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.shopping_list_dtos import ShoppingListEntryOutput
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.shopping_list_item import ShoppingListItem


class ShoppingListItemMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(
        item: ShoppingListItem, ingredient: Ingredient
    ) -> ShoppingListEntryOutput:
        quantity_needed = item.quantity_needed
        return ShoppingListEntryOutput(
            id=item.id,
            ingredient_id=item.ingredient_id,
            ingredient_name=ingredient.name,
            checked=item.checked,
            quantity_needed_amount=(
                quantity_needed.amount if quantity_needed else None
            ),
            quantity_needed_unit=(
                quantity_needed.unit.value if quantity_needed else None
            ),
        )
