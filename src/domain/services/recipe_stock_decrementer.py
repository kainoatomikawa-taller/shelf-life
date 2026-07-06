"""RecipeStockDecrementer domain service.

Powers the post-cook rating prompt's optional "update my pantry stock?"
offer (§5.6 AC2/AC3): identifies which of a user's inventory items were
called for by a just-cooked recipe and aren't already Out, so the rating
flow can suggest stepping them down (in -> low -> out) — the caller decides
whether to actually apply it, so the offer never becomes a forced action.

Pure logic, no I/O: the recipe and the user's inventory items are both
looked up by the caller and handed in.
"""

from __future__ import annotations

from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.value_objects.quantity_state import QuantityState


class RecipeStockDecrementer:
    """Selects the inventory items a recipe's ingredients make eligible for
    a one-step stock decrement."""

    @staticmethod
    def find_decrementable_items(
        recipe: Recipe, inventory_items: list[InventoryItem]
    ) -> list[InventoryItem]:
        """Inventory items whose ingredient the recipe calls for (essential
        or optional) and that aren't already Out — Out has nowhere further
        to step down to.
        """
        recipe_ingredient_ids = {i.ingredient_id for i in recipe.ingredients}
        return [
            item
            for item in inventory_items
            if item.ingredient_id in recipe_ingredient_ids
            and item.quantity_state is not QuantityState.OUT
        ]
