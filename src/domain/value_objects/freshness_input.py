"""FreshnessInput value object.

The raw signals computeFreshness needs to resolve a pantry item's freshness
date: an optional printed package date, an optional purchase date, the
ingredient's typical shelf life for its current and frozen storage, and
whether the item is currently frozen or has since thawed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FreshnessInput:
    package_date: date | None
    purchase_date: date | None
    storage_shelf_life_days: int | None
    freezer_shelf_life_days: int | None
    is_frozen: bool
    thawed_at: date | None = None
