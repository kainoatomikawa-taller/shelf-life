"""ShoppingListItem entity.

One ingredient a user has committed to buy after generating a Discover
recipe's shopping list (§5.4) and tapping "add". Recording which recipe
produced it is provenance only — it doesn't gate anything, so items from
different recipes calling for the same ingredient simply coexist.
"""

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import ValidationError


class ShoppingListItem:
    """A single ingredient a user needs to buy."""

    def __init__(
        self,
        id: str,
        user_id: str,
        ingredient_id: str,
        recipe_id: str,
        added_at: datetime,
    ) -> None:
        if not id:
            raise ValidationError("ShoppingListItem id is required.")
        if not user_id:
            raise ValidationError("ShoppingListItem user_id is required.")
        if not ingredient_id:
            raise ValidationError("ShoppingListItem ingredient_id is required.")
        if not recipe_id:
            raise ValidationError("ShoppingListItem recipe_id is required.")

        self._id = id
        self._user_id = user_id
        self._ingredient_id = ingredient_id
        self._recipe_id = recipe_id
        self._added_at = added_at

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
    def recipe_id(self) -> str:
        return self._recipe_id

    @property
    def added_at(self) -> datetime:
        return self._added_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ShoppingListItem):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
