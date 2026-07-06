"""GetCookNowFeed use case (§5.3).

Powers both tabs of the Cook Now screen from the same candidate pool:
recipes that survive the §10 Step 1 hard filter and classify as Cook Now
(§10 Step 2 — every essential ingredient is on hand or has a valid
substitution). "For You" orders that pool with RecipeScorer (§10 Step 3,
content-based); "Explore" orders it with ExploreFeedRanker (§10 Step 4,
popularity + adventurousness). Recipes classified Discover never appear
here — they belong to a separate "what could I cook if I shopped" surface,
not this one.

Every card's badges are derived from the same inputs the classifier/scorer
already computed internally, but those services only expose them as scores
or booleans — this use case re-derives the ingredient-level detail (which
ingredient is expiring, which is low, which needs which swap) needed to
render "Uses X — use it soon!", "N substitutions", and "You're low on Y".

Substitution suggestions are looked up in SubstitutionContext.GENERAL only.
This keeps a single ranking pass over mixed-context recipes simple at the
cost of not surfacing a recipe's baking- or savory-only swaps; every
GENERAL-context substitution in the catalog (the common case) still works.
"""

from __future__ import annotations

from src.application.dtos.cook_now_dtos import GetCookNowFeedInput, RecipeCardOutput
from src.application.mappers.recipe_card_mapper import RecipeCardMapper
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError, ValidationError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.explore_feed_ranker import ExploreFeedRanker
from src.domain.services.recipe_availability_classifier import (
    RecipeAvailabilityClassifier,
)
from src.domain.services.recipe_scorer import RecipeScorer
from src.domain.services.substitution_engine import SubstitutionEngine
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.recipe_availability import RecipeAvailability
from src.domain.value_objects.substitution_context import SubstitutionContext
from src.domain.value_objects.substitution_suggestion import SubstitutionSuggestion

_CONTEXT = SubstitutionContext.GENERAL

_EXPIRING_STATUSES_BY_URGENCY = (
    FreshnessDisplayStatus.USE_NOW,
    FreshnessDisplayStatus.USE_SOON,
)

_TABS = ("for_you", "explore")


class GetCookNowFeedUseCase:
    """Assemble one tab of the Cook Now feed for a user."""

    def __init__(
        self,
        recipe_repository: RecipeRepository,
        substitution_repository: SubstitutionRepository,
        ingredient_repository: IngredientRepository,
        inventory_item_repository: InventoryItemRepository,
        user_repository: UserRepository,
        classifier: RecipeAvailabilityClassifier | None = None,
        scorer: RecipeScorer | None = None,
        explore_ranker: ExploreFeedRanker | None = None,
        substitution_engine: SubstitutionEngine | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._substitution_repository = substitution_repository
        self._ingredient_repository = ingredient_repository
        self._inventory_item_repository = inventory_item_repository
        self._user_repository = user_repository
        self._classifier = classifier or RecipeAvailabilityClassifier()
        self._scorer = scorer or RecipeScorer()
        self._explore_ranker = explore_ranker or ExploreFeedRanker()
        self._substitution_engine = substitution_engine or SubstitutionEngine()

    async def execute(self, dto: GetCookNowFeedInput) -> list[RecipeCardOutput]:
        if dto.tab not in _TABS:
            raise ValidationError(f"tab must be one of {_TABS}, got '{dto.tab}'.")

        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        inventory_items = await self._inventory_item_repository.list_by_user(
            dto.user_id
        )
        available_ingredient_ids = {
            item.ingredient_id
            for item in inventory_items
            if item.quantity_state is not QuantityState.OUT
        }
        low_stock_ingredient_ids = {
            item.ingredient_id
            for item in inventory_items
            if item.quantity_state is QuantityState.LOW
        }
        freshness_by_ingredient_id = {
            item.ingredient_id: item.freshness_status
            for item in inventory_items
            if item.quantity_state is not QuantityState.OUT
        }

        recipes = await self._recipe_repository.list_all()
        if not recipes:
            return []

        essential_ingredient_ids = {
            recipe_ingredient.ingredient_id
            for recipe in recipes
            for recipe_ingredient in recipe.essential_ingredients()
        }
        candidates_by_ingredient_id = {
            ingredient_id: await self._substitution_repository.find_for_ingredient(
                ingredient_id
            )
            for ingredient_id in essential_ingredient_ids
        }

        needed_ingredient_ids = set(available_ingredient_ids)
        for recipe in recipes:
            needed_ingredient_ids.update(i.ingredient_id for i in recipe.ingredients)
        for candidates in candidates_by_ingredient_id.values():
            needed_ingredient_ids.update(c.to_ingredient_id for c in candidates)

        ingredients_by_id: dict[str, Ingredient] = {}
        for ingredient_id in needed_ingredient_ids:
            ingredient = await self._ingredient_repository.get_by_id(ingredient_id)
            if ingredient is not None:
                ingredients_by_id[ingredient_id] = ingredient

        survivors = self._classifier.filter_hard_constraints(
            recipes, user, ingredients_by_id
        )
        cook_now_recipes = [
            recipe
            for recipe in survivors
            if self._classifier.classify(
                recipe,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                context=_CONTEXT,
                candidates_by_ingredient_id=candidates_by_ingredient_id,
                ingredients_by_id=ingredients_by_id,
            )
            is RecipeAvailability.COOK_NOW
        ]
        if not cook_now_recipes:
            return []

        ordered_recipe_ids = self._rank(
            dto.tab,
            cook_now_recipes,
            user,
            available_ingredient_ids,
            freshness_by_ingredient_id,
            candidates_by_ingredient_id,
            ingredients_by_id,
        )
        recipes_by_id = {recipe.id: recipe for recipe in cook_now_recipes}

        return [
            self._to_card(
                recipes_by_id[recipe_id],
                user,
                available_ingredient_ids,
                low_stock_ingredient_ids,
                freshness_by_ingredient_id,
                candidates_by_ingredient_id,
                ingredients_by_id,
            )
            for recipe_id in ordered_recipe_ids
        ]

    def _rank(
        self,
        tab: str,
        recipes: list[Recipe],
        user: User,
        available_ingredient_ids: set[str],
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
        candidates_by_ingredient_id: dict[str, list],
        ingredients_by_id: dict[str, Ingredient],
    ) -> list[str]:
        if tab == "explore":
            scores = self._explore_ranker.rank(recipes, user)
        else:
            scores = self._scorer.score_all(
                recipes,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                freshness_by_ingredient_id=freshness_by_ingredient_id,
                context=_CONTEXT,
                candidates_by_ingredient_id=candidates_by_ingredient_id,
                ingredients_by_id=ingredients_by_id,
            )
        return [score.recipe_id for score in scores]

    def _to_card(
        self,
        recipe: Recipe,
        user: User,
        available_ingredient_ids: set[str],
        low_stock_ingredient_ids: set[str],
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
        candidates_by_ingredient_id: dict[str, list],
        ingredients_by_id: dict[str, Ingredient],
    ) -> RecipeCardOutput:
        recipe_ingredient_ids = [i.ingredient_id for i in recipe.ingredients]

        expiring_ingredient = self._most_urgent_expiring(
            recipe_ingredient_ids, freshness_by_ingredient_id, ingredients_by_id
        )
        low_stock_ingredient_id = next(
            (i for i in recipe_ingredient_ids if i in low_stock_ingredient_ids), None
        )
        low_stock_ingredient = (
            ingredients_by_id.get(low_stock_ingredient_id)
            if low_stock_ingredient_id
            else None
        )

        substitutions: list[tuple[str, SubstitutionSuggestion]] = []
        for recipe_ingredient in recipe.essential_ingredients():
            ingredient_id = recipe_ingredient.ingredient_id
            if ingredient_id in available_ingredient_ids:
                continue
            suggestions = self._substitution_engine.find_valid_substitutions(
                missing_ingredient_id=ingredient_id,
                context=_CONTEXT,
                user=user,
                available_ingredient_ids=available_ingredient_ids,
                candidates=candidates_by_ingredient_id.get(ingredient_id, []),
                ingredients_by_id=ingredients_by_id,
            )
            if suggestions:
                substitutions.append((ingredient_id, suggestions[0]))

        return RecipeCardMapper.to_output(
            recipe,
            expiring_ingredient,
            low_stock_ingredient,
            substitutions,
            ingredients_by_id,
        )

    @staticmethod
    def _most_urgent_expiring(
        recipe_ingredient_ids: list[str],
        freshness_by_ingredient_id: dict[str, FreshnessDisplayStatus],
        ingredients_by_id: dict[str, Ingredient],
    ) -> Ingredient | None:
        for status in _EXPIRING_STATUSES_BY_URGENCY:
            for ingredient_id in recipe_ingredient_ids:
                if freshness_by_ingredient_id.get(ingredient_id) is status:
                    return ingredients_by_id.get(ingredient_id)
        return None
