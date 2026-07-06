"""Use case tests for the Discover feed (§5.4), using in-memory repositories.

Covers all three acceptance criteria:
1. Only recipes classified Discover (a missing essential with no
   substitution) ever appear — Cook Now recipes are excluded.
2. "have X of Y" progress is computed across the full ingredient list.
3. Both tabs are backed by the correct ranking (For You = RecipeScorer,
   Explore = ExploreFeedRanker) over the same Discover candidate pool.
"""

from datetime import UTC, datetime

import pytest

from src.application.dtos.discover_dtos import GetDiscoverFeedInput
from src.application.use_cases.get_discover_feed import GetDiscoverFeedUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError, ValidationError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)
from tests.fakes.in_memory_recipe_repository import InMemoryRecipeRepository
from tests.fakes.in_memory_substitution_repository import (
    InMemorySubstitutionRepository,
)
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
STRAWBERRIES = "ingredient-strawberries"

USER_ID = "user-1"


def _ingredient(id: str, name: str | None = None) -> Ingredient:
    return Ingredient(
        id=id,
        name=name or id,
        aliases=[],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=[],
        diet_tags=[],
    )


def _inventory_item(
    ingredient_id: str,
    quantity_state: QuantityState = QuantityState.IN,
) -> InventoryItem:
    return InventoryItem(
        id=f"item-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        quantity_state=quantity_state,
        storage_location=StorageLocation.PANTRY,
        computed_freshness_date=datetime(2026, 1, 1, tzinfo=UTC).date(),
        freshness_date_type=FreshnessDateType.ESTIMATED_UNKNOWN,
        freshness_status=FreshnessDisplayStatus.FRESH,
        added_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-pancakes",
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(STRAWBERRIES, IngredientRole.OPTIONAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        flavor_profile=FlavorProfile(),
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user() -> User:
    return User(
        id=USER_ID, hard_constraints=HardConstraints(), preferences=SoftPreferences()
    )


async def _build_use_case(
    recipes: list[Recipe], inventory_items: list[InventoryItem]
) -> GetDiscoverFeedUseCase:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
        _ingredient(STRAWBERRIES, "Strawberries"),
    ]:
        await ingredient_repo.add(ingredient)

    recipe_repo = InMemoryRecipeRepository(recipes)
    substitution_repo = InMemorySubstitutionRepository([])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)
    user_repo = InMemoryUserRepository()
    await user_repo.add(_user())

    return GetDiscoverFeedUseCase(
        recipe_repository=recipe_repo,
        substitution_repository=substitution_repo,
        ingredient_repository=ingredient_repo,
        inventory_item_repository=inventory_repo,
        user_repository=user_repo,
    )


# --- AC1: only Discover recipes appear ---------------------------------------


@pytest.mark.asyncio
async def test_cook_now_recipes_are_excluded_from_the_feed() -> None:
    """A fully-stocked recipe never appears — this screen is Discover only."""
    fully_stocked = _recipe(id="recipe-fully-stocked")
    use_case = await _build_use_case(
        [fully_stocked],
        [_inventory_item(FLOUR), _inventory_item(EGGS), _inventory_item(MILK)],
    )
    cards = await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="for_you"))
    assert cards == []


@pytest.mark.asyncio
async def test_recipe_missing_an_essential_appears() -> None:
    missing_milk = _recipe(id="recipe-missing-milk")
    use_case = await _build_use_case(
        [missing_milk], [_inventory_item(FLOUR), _inventory_item(EGGS)]
    )
    cards = await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="for_you"))
    assert [c.id for c in cards] == ["recipe-missing-milk"]


@pytest.mark.asyncio
async def test_invalid_tab_raises_validation_error() -> None:
    use_case = await _build_use_case([_recipe()], [])
    with pytest.raises(ValidationError):
        await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="bogus"))


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case = await _build_use_case([_recipe()], [])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(GetDiscoverFeedInput(user_id="ghost", tab="for_you"))


# --- AC2: have X of Y progress ------------------------------------------------


@pytest.mark.asyncio
async def test_progress_reflects_have_and_total_counts() -> None:
    recipe = _recipe()  # 3 essential + 1 optional = 4 total
    use_case = await _build_use_case(
        [recipe], [_inventory_item(FLOUR), _inventory_item(EGGS)]
    )
    cards = await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="for_you"))
    assert cards[0].have_count == 2
    assert cards[0].total_count == 4


# --- AC3: both tabs, correct ranking ------------------------------------------


@pytest.mark.asyncio
async def test_for_you_tab_ranks_by_recipe_scorer() -> None:
    missing_milk = _recipe(id="recipe-missing-milk")
    use_case = await _build_use_case(
        [missing_milk], [_inventory_item(FLOUR), _inventory_item(EGGS)]
    )
    cards = await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="for_you"))
    assert [c.id for c in cards] == ["recipe-missing-milk"]


@pytest.mark.asyncio
async def test_explore_tab_ranks_by_explore_feed_ranker() -> None:
    missing_milk = _recipe(id="recipe-missing-milk", popularity_score=0.9)
    use_case = await _build_use_case(
        [missing_milk], [_inventory_item(FLOUR), _inventory_item(EGGS)]
    )
    cards = await use_case.execute(GetDiscoverFeedInput(user_id=USER_ID, tab="explore"))
    assert [c.id for c in cards] == ["recipe-missing-milk"]
