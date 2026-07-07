"""Data transfer objects for the post-cook rating prompt (§5.6).

Captures a star/thumb rating plus optional quick tags (AC1), and surfaces —
without ever applying — the recipe's ingredients that are eligible for the
optional pantry stock decrement (AC2), which only takes effect if the user
separately opts in via DecrementRecipeIngredientsUseCase (AC3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SubmitRatingInput:
    user_id: str
    recipe_id: str
    stars: int
    quick_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubmitRatingOutput:
    id: str
    user_id: str
    recipe_id: str
    stars: int
    quick_tags: list[str]
    made_it_at: datetime
    decrementable_ingredient_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DecrementRecipeIngredientsInput:
    user_id: str
    recipe_id: str


@dataclass(frozen=True)
class GetUserRatingsInput:
    user_id: str


@dataclass(frozen=True)
class RatingOutput:
    id: str
    user_id: str
    recipe_id: str
    stars: int
    quick_tags: list[str]
    made_it_at: datetime
