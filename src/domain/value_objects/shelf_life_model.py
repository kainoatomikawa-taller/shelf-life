"""ShelfLifeModel value object.

Distinguishes whether shelf-life values represent food-safety expiry
(spoilage) or quality/potency loss (potency). All spices use the
potency model — they remain safe indefinitely but lose flavour;
every other category defaults to spoilage.
"""

from __future__ import annotations

from enum import Enum


class ShelfLifeModel(str, Enum):
    SPOILAGE = "spoilage"
    POTENCY = "potency"
