"""IngredientRole value object.

Whether a recipe ingredient is required to make the dish at all (essential)
or a swap/garnish that can be left out without abandoning the recipe
(optional). This flag is not just descriptive — it decides how a recipe's
allergen and diet tags are derived from its ingredients (see
Recipe.derive_allergen_tags / derive_diet_tags).
"""

from __future__ import annotations

from enum import Enum


class IngredientRole(str, Enum):
    ESSENTIAL = "essential"
    OPTIONAL = "optional"
