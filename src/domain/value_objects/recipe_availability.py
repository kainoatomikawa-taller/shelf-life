"""RecipeAvailability value object.

The §10 Step 2 classification label for a recipe that has already survived
the hard-constraint filter: Cook Now when every essential ingredient is in
stock or substitutable right now, Discover otherwise.
"""

from __future__ import annotations

from enum import Enum


class RecipeAvailability(str, Enum):
    COOK_NOW = "cook_now"
    DISCOVER = "discover"
