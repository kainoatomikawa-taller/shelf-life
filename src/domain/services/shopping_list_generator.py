"""ShoppingListGenerator domain service.

Powers the Discover screen's per-recipe shopping list (§5.4): given a
recipe already classified Discover (RecipeAvailabilityClassifier — at
least one essential ingredient is neither on hand nor substitutable),
this service pinpoints every such ingredient — the "true gaps" the user
actually needs to buy (AC3) — and reports "have X of Y" progress across
the recipe's full ingredient list (AC2).

An essential ingredient only counts as a true gap when it's missing AND
has no valid substitution the user could make instead — the same test
RecipeScorer._classify_essentials applies for its missing/substitutable
split, but collected in full here rather than short-circuited, since
RecipeAvailabilityClassifier only needs to know *that* a recipe is
Discover, not the complete list of what's missing.

Optional ingredients never appear in the shopping list — they're never
inspected, exactly as in RecipeAvailabilityClassifier, so a recipe never
demands a purchase the cook doesn't strictly need (AC1).

Pure logic, no I/O: inventory availability, candidate substitutions, and
the ingredient catalog are all looked up by the caller and handed in,
exactly like SubstitutionEngine and RecipeAvailabilityClassifier before it.
"""

from __future__ import annotations

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.services.substitution_engine import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    SubstitutionEngine,
)
from src.domain.value_objects.recipe_ingredient_progress import (
    RecipeIngredientProgress,
)
from src.domain.value_objects.substitution_context import SubstitutionContext


class ShoppingListGenerator:
    """Computes a recipe's true ingredient gaps and have/total progress."""

    def __init__(self, substitution_engine: SubstitutionEngine | None = None) -> None:
        self._substitution_engine = substitution_engine or SubstitutionEngine()

    def true_gaps(
        self,
        recipe: Recipe,
        user: User,
        available_ingredient_ids: set[str],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> list[str]:
        """Essential ingredient ids the user must actually buy: not on
        hand and with no valid substitution either, in recipe order.
        """
        gaps: list[str] = []
        seen: set[str] = set()
        for recipe_ingredient in recipe.essential_ingredients():
            ingredient_id = recipe_ingredient.ingredient_id
            if ingredient_id in seen or ingredient_id in available_ingredient_ids:
                continue
            seen.add(ingredient_id)

            substitutes = self._substitution_engine.find_valid_substitutions(
                missing_ingredient_id=ingredient_id,
                context=context,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                candidates=candidates_by_ingredient_id.get(ingredient_id, []),
                ingredients_by_id=ingredients_by_id,
                confidence_threshold=confidence_threshold,
            )
            if not substitutes:
                gaps.append(ingredient_id)
        return gaps

    @staticmethod
    def progress(
        recipe: Recipe, available_ingredient_ids: set[str]
    ) -> RecipeIngredientProgress:
        """"have X of Y" across the recipe's full ingredient list (essential
        and optional together) — a whole-recipe shopping-trip view, not
        just the essentials §10 Step 2 cares about for classification.
        """
        ingredient_ids = {i.ingredient_id for i in recipe.ingredients}
        have_count = sum(1 for i in ingredient_ids if i in available_ingredient_ids)
        return RecipeIngredientProgress(
            have_count=have_count, total_count=len(ingredient_ids)
        )
