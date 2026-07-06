"""ShoppingListItem entity.

One ingredient a user has committed to buy, sourced either from a Discover
recipe's shopping list (§5.4, tapping "add") or from an ingredient newly
flagged Low/Out in the Kitchen inventory (§5.7 AC1). source_recipe_ids
records every recipe that has called for this ingredient — provenance
only, it doesn't gate anything, so items from different recipes calling
for the same ingredient simply coexist under one row. It is empty for
items sourced purely from a Low/Out inventory flag, which has no recipe
behind it. checked tracks whether the user has picked it up while shopping.
"""

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import ValidationError
from src.domain.value_objects.quantity import Quantity


class ShoppingListItem:
    """A single ingredient a user needs to buy."""

    def __init__(
        self,
        id: str,
        user_id: str,
        ingredient_id: str,
        source_recipe_ids: list[str],
        added_at: datetime,
        checked: bool = False,
        quantity_needed: Quantity | None = None,
    ) -> None:
        if not id:
            raise ValidationError("ShoppingListItem id is required.")
        if not user_id:
            raise ValidationError("ShoppingListItem user_id is required.")
        if not ingredient_id:
            raise ValidationError("ShoppingListItem ingredient_id is required.")

        self._id = id
        self._user_id = user_id
        self._ingredient_id = ingredient_id
        self._source_recipe_ids = list(source_recipe_ids)
        self._added_at = added_at
        self._checked = checked
        self._quantity_needed = quantity_needed

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def ingredient_id(self) -> str:
        return self._ingredient_id

    @property
    def source_recipe_ids(self) -> list[str]:
        return list(self._source_recipe_ids)

    @property
    def added_at(self) -> datetime:
        return self._added_at

    @property
    def checked(self) -> bool:
        return self._checked

    @property
    def quantity_needed(self) -> Quantity | None:
        return self._quantity_needed

    # --- Behaviour -----------------------------------------------------------

    def add_source_recipe(self, recipe_id: str) -> None:
        """Record another recipe that also calls for this ingredient."""
        if not recipe_id:
            raise ValidationError("recipe_id is required.")
        if recipe_id not in self._source_recipe_ids:
            self._source_recipe_ids.append(recipe_id)

    def mark_checked(self) -> None:
        self._checked = True

    def mark_unchecked(self) -> None:
        self._checked = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ShoppingListItem):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
