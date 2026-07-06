"""IngredientCategory value object.

Represents the five storage-based categories an ingredient can belong to.
Each category encodes both the ingredient's nature and its primary home.
"""

from __future__ import annotations

from enum import Enum


class IngredientCategory(str, Enum):
    PERISHABLE_FRIDGE = "perishable_fridge"
    PERISHABLE_COUNTER = "perishable_counter"
    FROZEN = "frozen"
    PANTRY = "pantry"
    SPICE = "spice"
