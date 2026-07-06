"""RecipeAvailabilityClassifier domain service.

Implements §10 Steps 1-2 of the recommendation pipeline:

1. Hard filter — a recipe whose derived allergen/diet tags cross a user's
   hard constraints (allergy or diet type) is excluded outright, no matter
   how well-stocked its ingredients are (AC1). This reuses
   Recipe.derive_allergen_tags/derive_diet_tags and
   HardConstraints.permits, so the rule stays in one place.
2. Availability classification — among recipes that survive the hard
   filter, a recipe is Cook Now when every ESSENTIAL ingredient is either
   already in stock or has a valid substitution the user can make right
   now (AC2, via SubstitutionEngine from §5.5); everything else is
   Discover. Optional ingredients are never even inspected, so they can
   never block a recipe from being Cook Now (AC3).

Pure logic, no I/O: inventory availability, the ingredient catalog, and
candidate substitutions are all looked up by the caller and handed in.
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
from src.domain.value_objects.recipe_availability import RecipeAvailability
from src.domain.value_objects.recipe_availability_result import (
    RecipeAvailabilityResult,
)
from src.domain.value_objects.substitution_context import SubstitutionContext


class RecipeAvailabilityClassifier:
    """Hard-filters recipes, then classifies survivors into Cook Now / Discover."""

    def __init__(self, substitution_engine: SubstitutionEngine | None = None) -> None:
        self._substitution_engine = substitution_engine or SubstitutionEngine()

    def filter_hard_constraints(
        self,
        recipes: list[Recipe],
        user: User,
        ingredients_by_id: dict[str, Ingredient],
    ) -> list[Recipe]:
        """Step 1: drop any recipe that violates the user's allergy or diet
        hard constraints (AC1).
        """
        return [
            recipe
            for recipe in recipes
            if user.hard_constraints.permits(
                recipe.derive_allergen_tags(ingredients_by_id),
                recipe.derive_diet_tags(ingredients_by_id),
            )
        ]

    def classify(
        self,
        recipe: Recipe,
        user: User,
        available_ingredient_ids: set[str],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> RecipeAvailability:
        """Step 2 for a single recipe. Assumes `recipe` has already cleared
        `filter_hard_constraints` — this method only judges availability.
        """
        for recipe_ingredient in recipe.essential_ingredients():
            if not self._is_available(
                recipe_ingredient.ingredient_id,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                context=context,
                candidates=candidates_by_ingredient_id.get(
                    recipe_ingredient.ingredient_id, []
                ),
                ingredients_by_id=ingredients_by_id,
                confidence_threshold=confidence_threshold,
            ):
                return RecipeAvailability.DISCOVER
        return RecipeAvailability.COOK_NOW

    def classify_recipes(
        self,
        recipes: list[Recipe],
        user: User,
        available_ingredient_ids: set[str],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> RecipeAvailabilityResult:
        """Run Steps 1 and 2 end to end: hard-filter `recipes`, then split
        the survivors into Cook Now / Discover.
        """
        survivors = self.filter_hard_constraints(recipes, user, ingredients_by_id)
        cook_now: list[Recipe] = []
        discover: list[Recipe] = []
        for recipe in survivors:
            bucket = self.classify(
                recipe,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                context=context,
                candidates_by_ingredient_id=candidates_by_ingredient_id,
                ingredients_by_id=ingredients_by_id,
                confidence_threshold=confidence_threshold,
            )
            target = cook_now if bucket is RecipeAvailability.COOK_NOW else discover
            target.append(recipe)
        return RecipeAvailabilityResult(
            cook_now=tuple(cook_now), discover=tuple(discover)
        )

    def _is_available(
        self,
        ingredient_id: str,
        user: User,
        available_ingredient_ids: set[str],
        context: SubstitutionContext,
        candidates: list[Substitution],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float,
    ) -> bool:
        if ingredient_id in available_ingredient_ids:
            return True
        substitutes = self._substitution_engine.find_valid_substitutions(
            missing_ingredient_id=ingredient_id,
            context=context,
            user=user,
            available_ingredient_ids=available_ingredient_ids,
            candidates=candidates,
            ingredients_by_id=ingredients_by_id,
            confidence_threshold=confidence_threshold,
        )
        return len(substitutes) > 0
