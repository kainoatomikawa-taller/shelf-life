"""RecipeAvailabilityResult value object.

The output of running §10 Steps 1-2 over a recipe list: recipes that
violated a hard constraint are simply absent — they appear in neither
bucket — and every survivor lands in exactly one of Cook Now or Discover.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.entities.recipe import Recipe


@dataclass(frozen=True)
class RecipeAvailabilityResult:
    cook_now: tuple[Recipe, ...] = field(default_factory=tuple)
    discover: tuple[Recipe, ...] = field(default_factory=tuple)
