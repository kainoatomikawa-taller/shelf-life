"""ShelfLifeByStorage value object.

Immutable record of how long an ingredient typically lasts in each
physical storage location. All values are in whole days; None means
the ingredient should not be stored in that location.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.storage_location import StorageLocation


@dataclass(frozen=True)
class ShelfLifeByStorage:
    fridge_days: int | None = None
    counter_days: int | None = None
    freezer_days: int | None = None
    pantry_days: int | None = None

    def for_location(self, location: StorageLocation) -> int | None:
        """Return the typical shelf life, in days, for the given location."""
        return {
            StorageLocation.FRIDGE: self.fridge_days,
            StorageLocation.COUNTER: self.counter_days,
            StorageLocation.FREEZER: self.freezer_days,
            StorageLocation.PANTRY: self.pantry_days,
        }[location]
