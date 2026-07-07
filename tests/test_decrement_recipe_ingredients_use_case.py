"""Use case tests for DecrementRecipeIngredients (§5.6 AC3)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.rating_dtos import DecrementRecipeIngredientsInput
from src.application.use_cases.decrement_recipe_ingredients import (
    DecrementRecipeIngredientsUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import RecipeNotFoundError, UserNotFoundError
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
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)
from tests.fakes.in_memory_recipe_repository import InMemoryRecipeRepository
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

USER_ID = "user-1"
RECIPE_ID = "recipe-pancakes"
FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
UNRELATED = "ingredient-unrelated"


def _ingredient(id: str, name: str) -> Ingredient:
    return Ingredient(
        id=id,
        name=name,
        aliases=[],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=[],
        diet_tags=[],
    )


def _recipe() -> Recipe:
    return Recipe(
        id=RECIPE_ID,
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
    )


def _inventory_item(
    ingredient_id: str, quantity_state: QuantityState
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


async def _build(inventory_items: list[InventoryItem]) -> tuple[
    DecrementRecipeIngredientsUseCase, InMemoryInventoryItemRepository
]:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(UNRELATED, "Unrelated"),
    ]:
        await ingredient_repo.add(ingredient)

    recipe_repo = InMemoryRecipeRepository([_recipe()])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)

    user_repo = InMemoryUserRepository()
    await user_repo.add(
        User(
            id=USER_ID,
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )
    )

    use_case = DecrementRecipeIngredientsUseCase(
        recipe_repository=recipe_repo,
        inventory_item_repository=inventory_repo,
        ingredient_repository=ingredient_repo,
        user_repository=user_repo,
    )
    return use_case, inventory_repo


@pytest.mark.asyncio
async def test_in_stock_ingredients_step_down_to_low() -> None:
    use_case, inventory_repo = await _build(
        [_inventory_item(FLOUR, QuantityState.IN)]
    )
    outputs = await use_case.execute(
        DecrementRecipeIngredientsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )

    assert [o.quantity_state for o in outputs] == ["low"]
    persisted = await inventory_repo.get_by_id("item-ingredient-flour")
    assert persisted is not None
    assert persisted.quantity_state == QuantityState.LOW


@pytest.mark.asyncio
async def test_low_stock_ingredients_step_down_to_out() -> None:
    use_case, inventory_repo = await _build(
        [_inventory_item(FLOUR, QuantityState.LOW)]
    )
    await use_case.execute(
        DecrementRecipeIngredientsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )

    persisted = await inventory_repo.get_by_id("item-ingredient-flour")
    assert persisted is not None
    assert persisted.quantity_state == QuantityState.OUT


@pytest.mark.asyncio
async def test_out_of_stock_ingredients_are_left_alone() -> None:
    use_case, _ = await _build([_inventory_item(FLOUR, QuantityState.OUT)])
    outputs = await use_case.execute(
        DecrementRecipeIngredientsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )
    assert outputs == []


@pytest.mark.asyncio
async def test_ingredients_not_in_the_recipe_are_left_alone() -> None:
    use_case, inventory_repo = await _build(
        [_inventory_item(UNRELATED, QuantityState.IN)]
    )
    outputs = await use_case.execute(
        DecrementRecipeIngredientsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )

    assert outputs == []
    persisted = await inventory_repo.get_by_id("item-ingredient-unrelated")
    assert persisted is not None
    assert persisted.quantity_state == QuantityState.IN


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case, _ = await _build([])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            DecrementRecipeIngredientsInput(user_id="ghost", recipe_id=RECIPE_ID)
        )


@pytest.mark.asyncio
async def test_unknown_recipe_raises_not_found() -> None:
    use_case, _ = await _build([])
    with pytest.raises(RecipeNotFoundError):
        await use_case.execute(
            DecrementRecipeIngredientsInput(
                user_id=USER_ID, recipe_id="ghost-recipe"
            )
        )
