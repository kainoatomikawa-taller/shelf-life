"""ShoppingListAggregator domain service.

Powers the Shopping List tab (§5.7 AC1): merges the explicit items a user
has already committed to buy (via Discover's one-tap add,
AddShoppingListItemsUseCase) with ingredients newly flagged Low or Out in
their Kitchen inventory, so a "need to buy" ingredient never appears twice
on the list regardless of where it was sourced from.

Pure logic, no I/O: the existing items and the low/out-flagged ingredient
ids are both looked up by the caller and handed in.
"""

from __future__ import annotations

from src.domain.entities.shopping_list_item import ShoppingListItem


class ShoppingListAggregator:
    """Determines which low/out-flagged ingredients still need a shopping
    list entry created for them."""

    @staticmethod
    def missing_low_stock_entries(
        existing_items: list[ShoppingListItem],
        low_stock_ingredient_ids: list[str],
    ) -> list[str]:
        """Low/out ingredient ids not already represented on the user's
        shopping list, de-duplicated and in the order given."""
        already_listed = {item.ingredient_id for item in existing_items}
        missing: list[str] = []
        for ingredient_id in low_stock_ingredient_ids:
            if ingredient_id in already_listed or ingredient_id in missing:
                continue
            missing.append(ingredient_id)
        return missing
