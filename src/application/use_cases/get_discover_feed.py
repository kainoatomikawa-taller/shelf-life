"""GetDiscoverFeed use case (§5.4).

Powers both tabs of the Discover screen from the same candidate pool:
recipes that survive the §10 Step 1 hard filter but classify as Discover
(§10 Step 2 — at least one essential ingredient is neither on hand nor
substitutable right now, AC1). This is the "what could I cook if I
shopped" surface GetCookNowFeedUseCase's docstring calls out as
deliberately excluded from Cook Now. "For You" orders the pool with
RecipeScorer (§10 Step 3); "Explore" orders it with ExploreFeedRanker
(§10 Step 4) — the same split Cook Now uses, just over the opposite
bucket.

Every card carries "have X of Y" progress (AC2) across the recipe's full
ingredient list via ShoppingListGenerator, so a shopper can see how close
they already are before tapping in for the per-recipe shopping list
(GenerateShoppingListForRecipeUseCase / AddShoppingListItemsUseCase).
"""

from __future__ import annotations

from src.application.dtos.discover_dtos import (
    DiscoverRecipeCardOutput,
    GetDiscoverFeedInput,
)
from src.application.mappers.discover_recipe_card_mapper import (
    DiscoverRecipeCardMapper,
)
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
from src.domain.services.shopping_list_generator import ShoppingListGenerator
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.substitution_context import SubstitutionContext

_CONTEXT = SubstitutionContext.GENERAL

_TABS = ("for_you", "explore")


class GetDiscoverFeedUseCase:
    """Assemble one tab of the Discover feed for a user."""

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
        shopping_list_generator: ShoppingListGenerator | None = None,
    ) -> None:
        self._recipe_repository = recipe_repository
        self._substitution_repository = substitution_repository
        self._ingredient_repository = ingredient_repository
        self._inventory_item_repository = inventory_item_repository
        self._user_repository = user_repository
        self._classifier = classifier or RecipeAvailabilityClassifier()
        self._scorer = scorer or RecipeScorer()
        self._explore_ranker = explore_ranker or ExploreFeedRanker()
        self._shopping_list_generator = (
            shopping_list_generator or ShoppingListGenerator()
        )

    async def execute(
        self, dto: GetDiscoverFeedInput
    ) -> list[DiscoverRecipeCardOutput]:
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

        result = self._classifier.classify_recipes(
            recipes,
            user=user,
            available_ingredient_ids=available_ingredient_ids,
            context=_CONTEXT,
            candidates_by_ingredient_id=candidates_by_ingredient_id,
            ingredients_by_id=ingredients_by_id,
        )
        discover_recipes = list(result.discover)
        if not discover_recipes:
            return []

        ordered_recipe_ids = self._rank(
            dto.tab,
            discover_recipes,
            user,
            available_ingredient_ids,
            freshness_by_ingredient_id,
            candidates_by_ingredient_id,
            ingredients_by_id,
        )
        recipes_by_id = {recipe.id: recipe for recipe in discover_recipes}

        return [
            DiscoverRecipeCardMapper.to_output(
                recipes_by_id[recipe_id],
                self._shopping_list_generator.progress(
                    recipes_by_id[recipe_id], available_ingredient_ids
                ),
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
