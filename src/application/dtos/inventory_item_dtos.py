"""Data transfer objects for the add-item use case (§5.2).

These are plain data contracts that cross the boundary between the interfaces
layer and the application layer. They never expose domain entities directly.

Only `user_id` and `ingredient_id` are required — every other field is
skippable from the add-item screen and falls back to a smart default derived
from the chosen ingredient's category (storage location) or a conservative
freshness estimate (purchase/package date left unset).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class AddInventoryItemInput:
    user_id: str
    ingredient_id: str
    quantity_state: str | None = None
    storage_location: str | None = None
    purchase_date: date | None = None
    printed_package_date: date | None = None
    is_frozen: bool = False
    notes: str | None = None


@dataclass(frozen=True)
class ListInventoryItemsInput:
    user_id: str


@dataclass(frozen=True)
class UpdateQuantityStateInput:
    """Input for the one-tap Mark Low / Mark Out quick actions (§5.2 AC2)."""

    item_id: str
    quantity_state: str


@dataclass(frozen=True)
class UpdateInventoryItemDatesInput:
    """Input for the "edit dates" quick action (§5.2). Both dates are
    replaced wholesale — pass None to clear a date."""

    item_id: str
    purchase_date: date | None = None
    printed_package_date: date | None = None


@dataclass(frozen=True)
class RemoveInventoryItemInput:
    """Input for the "used it up" / "delete" quick actions (§5.2 AC2):
    both remove the item outright, once it's no longer worth tracking."""

    item_id: str


@dataclass(frozen=True)
class SpoilageCheckTipOutput:
    smell: str
    look: str
    texture: str


@dataclass(frozen=True)
class InventoryItemOutput:
    id: str
    user_id: str
    ingredient_id: str
    ingredient_name: str
    ingredient_category: str
    quantity_state: str
    storage_location: str
    purchase_date: date | None
    printed_package_date: date | None
    is_frozen: bool
    computed_freshness_date: date
    freshness_date_type: str
    freshness_date_label: str
    freshness_date_tooltip: str
    freshness_status: str
    spoilage_check_tip: SpoilageCheckTipOutput | None
    added_at: datetime
    notes: str | None
