"""ExploreFeedRanker domain service.

Implements §10 Step 4: ranks the Explore feed primarily by a recipe's
popularity, then mixes in out-of-comfort-zone recipes scaled by the user's
adventurousness slider. Assumes `recipes` has already survived the §10
Step 1 hard filter (RecipeAvailabilityClassifier), exactly like RecipeScorer
does for §10 Step 3.

* popularity   — recipe.popularity_score, clamped to [0.0, 1.0] (AC1). This
                 is the dominant term in total_score, so Explore ranks
                 primarily by popularity.
* novelty      — how far a recipe's flavor profile sits from the user's
                 TasteVector: 0.0 is an exact match ("in comfort zone"),
                 1.0 is maximally different. The mirror image of the
                 taste-similarity RecipeScorer computes for §10 Step 3
                 (AC1, AC3).
* novelty_fit  — how close a recipe's novelty is to the *target* novelty
                 the user's adventurousness slider calls for. The target
                 scales linearly from MIN_NOVELTY_TARGET up to
                 MAX_NOVELTY_TARGET as adventurousness goes from 0.0 to
                 1.0 — never all the way down to 0.0, so even a fully
                 cautious slider still surfaces recipes that are adjacent
                 to the user's usual taste rather than pure repeats of it,
                 and never all the way up to 1.0, so a fully adventurous
                 slider still favors recipes with *some* relation to the
                 user's palate over the most jarring possible ones (AC2,
                 AC3).

total_score blends popularity and novelty_fit with popularity weighted
higher (AC1), so novelty only nudges the ranking within a popularity band
rather than overriding it.

Pure logic, no I/O: the recipe list and user are handed in by the caller,
exactly like RecipeAvailabilityClassifier and RecipeScorer before it.
"""

from __future__ import annotations

import math

from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError
from src.domain.value_objects.explore_score import ExploreScore
from src.domain.value_objects.flavor_profile import FLAVOR_DIMENSIONS

DEFAULT_WEIGHTS: dict[str, float] = {
    "popularity": 0.65,
    "novelty_fit": 0.35,
}

_WEIGHT_TOLERANCE = 1e-6

MIN_NOVELTY_TARGET = 0.15
MAX_NOVELTY_TARGET = 0.95


class ExploreFeedRanker:
    """Ranks recipes for the Explore feed: popularity first, then novelty
    scaled by adventurousness.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights or DEFAULT_WEIGHTS
        if set(self._weights) != set(DEFAULT_WEIGHTS):
            raise ValidationError(
                f"ExploreFeedRanker weights must have exactly the keys "
                f"{sorted(DEFAULT_WEIGHTS)}, got {sorted(self._weights)}."
            )
        if abs(sum(self._weights.values()) - 1.0) > _WEIGHT_TOLERANCE:
            raise ValidationError(
                f"ExploreFeedRanker weights must sum to 1.0, got "
                f"{sum(self._weights.values())}."
            )

    def score(self, recipe: Recipe, user: User) -> ExploreScore:
        popularity = min(1.0, max(0.0, recipe.popularity_score))
        novelty = self._novelty_score(recipe, user)
        novelty_fit = self._novelty_fit_score(novelty, user.preferences.adventurousness)
        total = (
            self._weights["popularity"] * popularity
            + self._weights["novelty_fit"] * novelty_fit
        )
        return ExploreScore(
            recipe_id=recipe.id,
            popularity_score=popularity,
            novelty_score=novelty,
            novelty_fit_score=novelty_fit,
            total_score=total,
        )

    def rank(self, recipes: list[Recipe], user: User) -> list[ExploreScore]:
        """Score every recipe, most recommended first.

        Ties in total_score fall back to popularity_score, keeping
        popularity the primary sort key end to end (AC1).
        """
        scores = [self.score(recipe, user) for recipe in recipes]
        return sorted(
            scores, key=lambda s: (s.total_score, s.popularity_score), reverse=True
        )

    # --- Novelty -----------------------------------------------------------

    @staticmethod
    def _novelty_score(recipe: Recipe, user: User) -> float:
        """0.0 for a recipe whose flavor profile exactly matches the user's
        TasteVector, 1.0 for a maximally different one, via normalized
        Euclidean distance across the FLAVOR_DIMENSIONS.
        """
        user_weights = user.taste_vector.weights
        recipe_weights = recipe.flavor_profile.as_tuple()
        squared_diff: float = sum(
            (u - r) ** 2 for u, r in zip(user_weights, recipe_weights, strict=True)
        )
        distance = math.sqrt(squared_diff)
        max_distance = math.sqrt(len(FLAVOR_DIMENSIONS))
        return distance / max_distance

    @staticmethod
    def _novelty_fit_score(novelty: float, adventurousness: float) -> float:
        """1.0 when `novelty` exactly matches the target novelty the user's
        adventurousness slider calls for, decaying linearly the further it
        drifts away in either direction.
        """
        target = MIN_NOVELTY_TARGET + adventurousness * (
            MAX_NOVELTY_TARGET - MIN_NOVELTY_TARGET
        )
        return 1.0 - abs(novelty - target)
