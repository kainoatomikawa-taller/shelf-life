"""Data transfer objects for the recipe detail use case (§5.4 follow-on):
the full ingredient list and procedure behind a Discover/Cook Now card,
shown once a user taps into a recipe.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GetRecipeDetailInput:
    recipe_id: str


@dataclass(frozen=True)
class RecipeIngredientDetailOutput:
    ingredient_id: str
    ingredient_name: str
    role: str  # "essential" | "optional"


@dataclass(frozen=True)
class RecipeDetailOutput:
    id: str
    name: str
    time_minutes: int
    difficulty: str
    cuisine_tags: list[str] = field(default_factory=list)
    ingredients: list[RecipeIngredientDetailOutput] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
