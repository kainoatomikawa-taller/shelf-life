"""StorageLocation value object.

The physical location where an ingredient is kept. Used for
defaultStorageLocation and as the key into typicalShelfLifeByStorage.
"""

from __future__ import annotations

from enum import Enum


class StorageLocation(str, Enum):
    FRIDGE = "fridge"
    COUNTER = "counter"
    FREEZER = "freezer"
    PANTRY = "pantry"
