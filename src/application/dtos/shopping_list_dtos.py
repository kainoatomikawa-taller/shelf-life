"""Data transfer objects for the Shopping List tab (§5.7).

Aggregates Discover-sourced items (AddShoppingListItemsUseCase) with
ingredients flagged Low/Out in the Kitchen inventory (AC1), tracks
check-off state while shopping (AC2), and closes the loop by turning
checked-off purchases into Kitchen inventory items dated today (AC3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from src.application.dtos.inventory_item_dtos import InventoryItemOutput


@dataclass(frozen=True)
class GetShoppingListInput:
    user_id: str


@dataclass(frozen=True)
class ShoppingListEntryOutput:
    id: str
    ingredient_id: str
    ingredient_name: str
    checked: bool
    quantity_needed_amount: float | None = None
    quantity_needed_unit: str | None = None


@dataclass(frozen=True)
class CheckShoppingListItemInput:
    item_id: str
    checked: bool


@dataclass(frozen=True)
class AddPurchasesToKitchenInput:
    user_id: str
    purchase_date: date | None = None


@dataclass(frozen=True)
class AddPurchasesToKitchenOutput:
    added_items: list[InventoryItemOutput] = field(default_factory=list)
