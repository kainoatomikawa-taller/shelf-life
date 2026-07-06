"""RecipeIngredientProgress value object.

The Discover screen's "have X of Y" badge (§5.4): how many of a recipe's
ingredients — essential and optional together — the user already has on
hand, out of the total the recipe calls for.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeIngredientProgress:
    have_count: int
    total_count: int
