"""RecipeScore value object.

The §10 Step 3 output for one recipe: each sub-score in [0.0, 1.0] alongside
the weighted total, kept separate so a caller (or a support engineer
debugging a weird ranking) can see exactly why a recipe landed where it did
rather than trusting an opaque number.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeScore:
    recipe_id: str
    taste_score: float
    effort_score: float
    freshness_score: float
    substitution_penalty_score: float
    budget_fit_score: float
    total_score: float
