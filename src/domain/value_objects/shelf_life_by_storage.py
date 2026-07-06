"""ShelfLifeByStorage value object.

Immutable record of how long an ingredient typically lasts in each
physical storage location. All values are in whole days; None means
the ingredient should not be stored in that location.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShelfLifeByStorage:
    fridge_days: int | None = None
    counter_days: int | None = None
    freezer_days: int | None = None
    pantry_days: int | None = None
