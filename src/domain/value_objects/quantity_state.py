"""QuantityState value object.

A coarse, user-reported read on how much of an inventory item is left.
Unlike PantryItem's precise Quantity (amount + unit), this is a deliberately
low-friction three-value signal — most users can say "in/low/out" at a
glance without ever weighing or measuring anything.
"""

from __future__ import annotations

from enum import Enum


class QuantityState(str, Enum):
    IN = "in"
    LOW = "low"
    OUT = "out"
