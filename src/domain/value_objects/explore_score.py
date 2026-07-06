"""ExploreScore value object.

The §10 Step 4 output for one recipe: popularity and novelty sub-scores
alongside the weighted total, kept separate for the same reason as
RecipeScore — so a caller can see why a recipe landed where it did rather
than trusting an opaque number.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExploreScore:
    recipe_id: str
    popularity_score: float
    novelty_score: float
    novelty_fit_score: float
    total_score: float
