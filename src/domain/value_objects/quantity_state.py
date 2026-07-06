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

    def step_down(self) -> QuantityState:
        """One step down the in -> low -> out ladder; out is a floor.

        Powers the post-cook rating prompt's optional stock decrement
        (§5.6 AC3): using up some of an ingredient nudges it toward out
        without skipping straight there.
        """
        if self is QuantityState.IN:
            return QuantityState.LOW
        return QuantityState.OUT
