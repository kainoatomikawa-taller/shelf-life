"""RecipeScorer domain service.

Implements §10 Step 3: scores a recipe that has already survived the §10
Step 1 hard filter (RecipeAvailabilityClassifier) as a weighted blend of:

* taste       — similarity between the user's TasteVector and the recipe's
                FlavorProfile (AC1).
* effort      — how well recipe.time_minutes/difficulty/equipment_needed
                fit the user's available time, skill level, and equipment
                (AC1).
* freshness   — a boost for recipes that use ingredients the user's
                inventory shows as expiring soon or now, so cooking them
                measurably outranks an otherwise-identical recipe that
                doesn't touch anything expiring (AC1, AC3).
* substitution_penalty — reduced for recipes that lean on substitutions
                rather than the genuine essential ingredient, even when
                that substitution is itself valid and available (AC1).
* budget_fit  — reduced by essential ingredients that are neither on hand
                nor substitutable at all (i.e. must be bought). Rewards
                fewer such items, and cheaper ones when a cost lookup is
                supplied; degrades gracefully to a uniform per-item cost
                when it isn't (AC2). This is the only component that can
                ever move below 1.0 for a Discover recipe specifically —
                a Cook Now recipe has no missing essentials by definition.

Pure logic, no I/O: inventory availability, freshness status, the
ingredient catalog, and candidate substitutions are all looked up by the
caller and handed in, exactly like SubstitutionEngine and
RecipeAvailabilityClassifier before it.
"""

from __future__ import annotations

import math

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError
from src.domain.services.substitution_engine import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    SubstitutionEngine,
)
from src.domain.value_objects.budget_sensitivity import BudgetSensitivity
from src.domain.value_objects.flavor_profile import FLAVOR_DIMENSIONS, FlavorProfile
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.recipe_score import RecipeScore
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.substitution_context import SubstitutionContext
from src.domain.value_objects.taste_vector import TasteVector

DEFAULT_WEIGHTS: dict[str, float] = {
    "taste": 0.35,
    "effort": 0.20,
    "freshness": 0.15,
    "substitution_penalty": 0.10,
    "budget_fit": 0.20,
}

_WEIGHT_TOLERANCE = 1e-6

_DIFFICULTY_ORDER = {
    SkillLevel.BEGINNER: 0,
    SkillLevel.INTERMEDIATE: 1,
    SkillLevel.ADVANCED: 2,
}
_DIFFICULTY_PENALTY_PER_LEVEL = 0.5

_FRESHNESS_URGENCY = {
    FreshnessDisplayStatus.USE_NOW: 1.0,
    FreshnessDisplayStatus.USE_SOON: 0.6,
    FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT: 0.3,
    FreshnessDisplayStatus.FRESH: 0.0,
}

_BUDGET_SENSITIVITY_MULTIPLIER = {
    BudgetSensitivity.LOW: 0.5,
    BudgetSensitivity.MEDIUM: 1.0,
    BudgetSensitivity.HIGH: 1.5,
}

_DEFAULT_INGREDIENT_COST = 1.0


class RecipeScorer:
    """Scores recipes as a weighted blend of taste, effort, freshness,
    substitution penalty, and budget fit.
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        substitution_engine: SubstitutionEngine | None = None,
    ) -> None:
        self._weights = weights or DEFAULT_WEIGHTS
        if set(self._weights) != set(DEFAULT_WEIGHTS):
            raise ValidationError(
                f"RecipeScorer weights must have exactly the keys "
                f"{sorted(DEFAULT_WEIGHTS)}, got {sorted(self._weights)}."
            )
        if abs(sum(self._weights.values()) - 1.0) > _WEIGHT_TOLERANCE:
            raise ValidationError(
                f"RecipeScorer weights must sum to 1.0, got "
                f"{sum(self._weights.values())}."
            )
        self._substitution_engine = substitution_engine or SubstitutionEngine()

    def score(
        self,
        recipe: Recipe,
        user: User,
        available_ingredient_ids: set[str],
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        ingredient_cost_by_id: dict[str, float] | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> RecipeScore:
        essential_ids = [i.ingredient_id for i in recipe.essential_ingredients()]
        substitutable_ids, missing_ids = self._classify_essentials(
            essential_ids,
            user=user,
            available_ingredient_ids=available_ingredient_ids,
            context=context,
            candidates_by_ingredient_id=candidates_by_ingredient_id,
            ingredients_by_id=ingredients_by_id,
            confidence_threshold=confidence_threshold,
        )

        taste = self._taste_score(user.taste_vector, recipe.flavor_profile)
        effort = self._effort_score(recipe, user.preferences)
        freshness = self._freshness_score(recipe, freshness_by_ingredient_id)
        substitution_penalty = self._substitution_penalty_score(
            len(essential_ids), len(substitutable_ids)
        )
        budget_fit = self._budget_fit_score(
            essential_ids,
            missing_ids,
            ingredient_cost_by_id,
            user.preferences.budget_sensitivity,
        )

        total = (
            self._weights["taste"] * taste
            + self._weights["effort"] * effort
            + self._weights["freshness"] * freshness
            + self._weights["substitution_penalty"] * substitution_penalty
            + self._weights["budget_fit"] * budget_fit
        )
        return RecipeScore(
            recipe_id=recipe.id,
            taste_score=taste,
            effort_score=effort,
            freshness_score=freshness,
            substitution_penalty_score=substitution_penalty,
            budget_fit_score=budget_fit,
            total_score=total,
        )

    def score_all(
        self,
        recipes: list[Recipe],
        user: User,
        available_ingredient_ids: set[str],
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        ingredient_cost_by_id: dict[str, float] | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> list[RecipeScore]:
        """Score every recipe, most recommended first."""
        scores = [
            self.score(
                recipe,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                freshness_by_ingredient_id=freshness_by_ingredient_id,
                context=context,
                candidates_by_ingredient_id=candidates_by_ingredient_id,
                ingredients_by_id=ingredients_by_id,
                ingredient_cost_by_id=ingredient_cost_by_id,
                confidence_threshold=confidence_threshold,
            )
            for recipe in recipes
        ]
        return sorted(scores, key=lambda s: s.total_score, reverse=True)

    # --- Taste ---------------------------------------------------------------

    @staticmethod
    def _taste_score(
        taste_vector: TasteVector, recipe_flavor_profile: FlavorProfile
    ) -> float:
        """1.0 for an identical flavor profile, 0.0 for maximally opposite,
        via normalized Euclidean distance across the FLAVOR_DIMENSIONS.
        """
        recipe_weights = recipe_flavor_profile.as_tuple()
        squared_diff: float = sum(
            (u - r) ** 2
            for u, r in zip(taste_vector.weights, recipe_weights, strict=True)
        )
        distance = math.sqrt(squared_diff)
        max_distance = math.sqrt(len(FLAVOR_DIMENSIONS))
        return 1.0 - distance / max_distance

    # --- Effort ----------------------------------------------------------------

    @classmethod
    def _effort_score(cls, recipe: Recipe, preferences: SoftPreferences) -> float:
        return (
            cls._time_fit(recipe, preferences)
            + cls._difficulty_fit(recipe, preferences)
            + cls._equipment_fit(recipe, preferences)
        ) / 3

    @staticmethod
    def _time_fit(recipe: Recipe, preferences: SoftPreferences) -> float:
        return min(
            1.0, preferences.typical_time_available_minutes / recipe.time_minutes
        )

    @staticmethod
    def _difficulty_fit(recipe: Recipe, preferences: SoftPreferences) -> float:
        gap = (
            _DIFFICULTY_ORDER[recipe.difficulty]
            - _DIFFICULTY_ORDER[preferences.skill_level]
        )
        if gap <= 0:
            return 1.0
        return max(0.0, 1.0 - _DIFFICULTY_PENALTY_PER_LEVEL * gap)

    @staticmethod
    def _equipment_fit(recipe: Recipe, preferences: SoftPreferences) -> float:
        needed = set(recipe.equipment_needed)
        if not needed:
            return 1.0
        have = set(preferences.equipment)
        return len(needed & have) / len(needed)

    # --- Freshness ---------------------------------------------------------------

    @staticmethod
    def _freshness_score(
        recipe: Recipe,
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
    ) -> float:
        """Sum of urgency across every ingredient (essential or optional)
        this recipe calls for that's also in the user's inventory, capped
        at 1.0 — a recipe using two expiring ingredients outscores one
        using a single expiring ingredient (AC3), up to the cap.
        """
        ingredient_ids = {i.ingredient_id for i in recipe.ingredients}
        urgency = sum(
            _FRESHNESS_URGENCY[freshness_by_ingredient_id[ingredient_id]]
            for ingredient_id in ingredient_ids
            if ingredient_id in freshness_by_ingredient_id
        )
        return min(1.0, urgency)

    # --- Substitution penalty + budget fit --------------------------------------

    def _classify_essentials(
        self,
        essential_ids: list[str],
        user: User,
        available_ingredient_ids: set[str],
        context: SubstitutionContext,
        candidates_by_ingredient_id: dict[str, list[Substitution]],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float,
    ) -> tuple[list[str], list[str]]:
        """Split essential ingredients not directly on hand into
        (substitutable, missing) — missing means no valid substitution
        exists either, so it would have to be bought.
        """
        substitutable: list[str] = []
        missing: list[str] = []
        for ingredient_id in essential_ids:
            if ingredient_id in available_ingredient_ids:
                continue
            substitutes = self._substitution_engine.find_valid_substitutions(
                missing_ingredient_id=ingredient_id,
                context=context,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                candidates=candidates_by_ingredient_id.get(ingredient_id, []),
                ingredients_by_id=ingredients_by_id,
                confidence_threshold=confidence_threshold,
            )
            (substitutable if substitutes else missing).append(ingredient_id)
        return substitutable, missing

    @staticmethod
    def _substitution_penalty_score(
        essential_count: int, substitutable_count: int
    ) -> float:
        if essential_count == 0:
            return 1.0
        return 1.0 - (substitutable_count / essential_count)

    @staticmethod
    def _budget_fit_score(
        essential_ids: list[str],
        missing_ids: list[str],
        ingredient_cost_by_id: dict[str, float] | None,
        budget_sensitivity: BudgetSensitivity,
    ) -> float:
        if not missing_ids:
            return 1.0
        cost_by_id = ingredient_cost_by_id or {}
        total_cost = sum(
            cost_by_id.get(i, _DEFAULT_INGREDIENT_COST) for i in essential_ids
        )
        if total_cost <= 0:
            return 1.0
        missing_cost = sum(
            cost_by_id.get(i, _DEFAULT_INGREDIENT_COST) for i in missing_ids
        )
        multiplier = _BUDGET_SENSITIVITY_MULTIPLIER[budget_sensitivity]
        return max(0.0, 1.0 - (missing_cost / total_cost) * multiplier)
