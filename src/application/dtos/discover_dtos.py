"""Data transfer objects for the Discover feed and its per-recipe shopping
list use cases (§5.4).

Discover cards carry "have X of Y" progress instead of the Cook Now feed's
availability badges, since every Discover recipe is missing at least one
essential by definition — the interesting signal here is how close the
user already is, not why it's cookable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GetDiscoverFeedInput:
    user_id: str
    tab: str  # "for_you" | "explore"


@dataclass(frozen=True)
class DiscoverRecipeCardOutput:
    id: str
    name: str
    time_minutes: int
    difficulty: str
    cuisine_tags: list[str] = field(default_factory=list)
    have_count: int = 0
    total_count: int = 0


@dataclass(frozen=True)
class GenerateShoppingListInput:
    user_id: str
    recipe_id: str


@dataclass(frozen=True)
class AddShoppingListItemsInput:
    user_id: str
    recipe_id: str


@dataclass(frozen=True)
class ShoppingListItemOutput:
    ingredient_id: str
    ingredient_name: str


@dataclass(frozen=True)
class ShoppingListOutput:
    recipe_id: str
    items: list[ShoppingListItemOutput] = field(default_factory=list)
