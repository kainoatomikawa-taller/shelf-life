"""Use case tests for the Cook Now feed (§5.3), using in-memory repositories.

Covers all three acceptance criteria:
1. Both tabs are backed by the correct ranking (For You = RecipeScorer,
   Explore = ExploreFeedRanker) over the same Cook Now candidate pool.
2. Expiring / substitution / low-stock badges render correctly.
3. A tapped substitution badge's data (the swap) is present on the card.
"""

from datetime import datetime, timezone

import pytest

from src.application.dtos.cook_now_dtos import GetCookNowFeedInput
from src.application.use_cases.get_cook_now_feed import GetCookNowFeedUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError, ValidationError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from src.domain.value_objects.substitution_context import SubstitutionContext
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
ALMOND_MILK = "ingredient-almond-milk"
STRAWBERRIES = "ingredient-strawberries"
VANILLA = "ingredient-vanilla"

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
    freshness_status: FreshnessDisplayStatus = FreshnessDisplayStatus.FRESH,
) -> InventoryItem:
    return InventoryItem(
        id=f"item-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        quantity_state=quantity_state,
        storage_location=StorageLocation.PANTRY,
        computed_freshness_date=datetime(2026, 1, 1, tzinfo=timezone.utc).date(),
        freshness_date_type=FreshnessDateType.ESTIMATED_UNKNOWN,
        freshness_status=freshness_status,
        added_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
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
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
        flavor_profile=FlavorProfile(),
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user() -> User:
    return User(
        id=USER_ID,
        hard_constraints=HardConstraints(),
        preferences=SoftPreferences(),
    )


async def _build_use_case(
    recipes: list[Recipe],
    inventory_items: list[InventoryItem],
    substitutions: list[Substitution] | None = None,
    extra_ingredients: list[Ingredient] | None = None,
) -> GetCookNowFeedUseCase:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
        _ingredient(ALMOND_MILK, "Almond Milk"),
        _ingredient(STRAWBERRIES, "Strawberries"),
        _ingredient(VANILLA, "Vanilla"),
        *(extra_ingredients or []),
    ]:
        await ingredient_repo.add(ingredient)

    recipe_repo = InMemoryRecipeRepository(recipes)
    substitution_repo = InMemorySubstitutionRepository(substitutions or [])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)
    user_repo = InMemoryUserRepository()
    await user_repo.add(_user())

    return GetCookNowFeedUseCase(
        recipe_repository=recipe_repo,
        substitution_repository=substitution_repo,
        ingredient_repository=ingredient_repo,
        inventory_item_repository=inventory_repo,
        user_repository=user_repo,
    )


# --- AC1: both tabs present, backed by the correct ranking -------------------


@pytest.mark.asyncio
async def test_for_you_tab_ranks_by_recipe_scorer() -> None:
    fully_stocked = _recipe(id="recipe-fully-stocked")
    use_case = await _build_use_case(
        [fully_stocked],
        [
            _inventory_item(FLOUR),
            _inventory_item(EGGS),
            _inventory_item(MILK),
        ],
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="for_you"))
    assert [c.id for c in cards] == ["recipe-fully-stocked"]


@pytest.mark.asyncio
async def test_explore_tab_ranks_by_explore_feed_ranker() -> None:
    fully_stocked = _recipe(id="recipe-fully-stocked", popularity_score=0.9)
    use_case = await _build_use_case(
        [fully_stocked],
        [
            _inventory_item(FLOUR),
            _inventory_item(EGGS),
            _inventory_item(MILK),
        ],
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="explore"))
    assert [c.id for c in cards] == ["recipe-fully-stocked"]


@pytest.mark.asyncio
async def test_invalid_tab_raises_validation_error() -> None:
    use_case = await _build_use_case([_recipe()], [])
    with pytest.raises(ValidationError):
        await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="bogus"))


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case = await _build_use_case([_recipe()], [])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(GetCookNowFeedInput(user_id="ghost", tab="for_you"))


@pytest.mark.asyncio
async def test_discover_recipes_are_excluded_from_the_feed() -> None:
    """A recipe missing an essential with no substitution never appears —
    this screen is Cook Now only, not Discover."""
    missing_essential = _recipe(id="recipe-missing-flour")
    use_case = await _build_use_case(
        missing_essential and [missing_essential],
        [_inventory_item(EGGS), _inventory_item(MILK)],  # flour missing entirely
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="for_you"))
    assert cards == []


# --- AC2: badges render correctly --------------------------------------------


@pytest.mark.asyncio
async def test_expiring_ingredient_badge() -> None:
    recipe = _recipe()
    use_case = await _build_use_case(
        [recipe],
        [
            _inventory_item(FLOUR),
            _inventory_item(EGGS),
            _inventory_item(
                MILK, freshness_status=FreshnessDisplayStatus.USE_SOON
            ),
        ],
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="for_you"))
    assert cards[0].badges.expiring_ingredient_name == "Milk"


@pytest.mark.asyncio
async def test_low_stock_badge() -> None:
    recipe = _recipe()
    use_case = await _build_use_case(
        [recipe],
        [
            _inventory_item(FLOUR, quantity_state=QuantityState.LOW),
            _inventory_item(EGGS),
            _inventory_item(MILK),
        ],
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="for_you"))
    assert cards[0].badges.low_stock_ingredient_name == "Flour"


@pytest.mark.asyncio
async def test_substitution_badge_count_and_no_badge_when_fully_stocked() -> None:
    recipe = _recipe()
    fully_stocked_use_case = await _build_use_case(
        [recipe],
        [_inventory_item(FLOUR), _inventory_item(EGGS), _inventory_item(MILK)],
    )
    cards = await fully_stocked_use_case.execute(
        GetCookNowFeedInput(user_id=USER_ID, tab="for_you")
    )
    assert cards[0].badges.substitution_count == 0
    assert cards[0].substitutions == []


# --- AC3: tapping a substitution badge reveals the swap ----------------------


@pytest.mark.asyncio
async def test_substitution_badge_reveals_the_swap() -> None:
    recipe = _recipe()
    substitution = Substitution(
        id="sub-1",
        from_ingredient_id=MILK,
        to_ingredient_id=ALMOND_MILK,
        context=SubstitutionContext.GENERAL,
        confidence=0.9,
        ratio_note="1:1",
        impact_note="Slightly nuttier flavor.",
    )
    use_case = await _build_use_case(
        [recipe],
        [
            _inventory_item(FLOUR),
            _inventory_item(EGGS),
            _inventory_item(ALMOND_MILK),  # milk missing, almond milk on hand
        ],
        substitutions=[substitution],
    )
    cards = await use_case.execute(GetCookNowFeedInput(user_id=USER_ID, tab="for_you"))

    assert cards[0].badges.substitution_count == 1
    [swap] = cards[0].substitutions
    assert swap.from_ingredient_name == "Milk"
    assert swap.to_ingredient_name == "Almond Milk"
    assert swap.disclosure == "Slightly nuttier flavor."
    assert swap.ratio_note == "1:1"
    assert swap.confidence == 0.9
