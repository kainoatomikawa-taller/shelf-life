"""Use case tests for AddShoppingListItems (§5.4 AC3 — one-tap add)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.discover_dtos import AddShoppingListItemsInput
from src.application.use_cases.add_shopping_list_items import (
    AddShoppingListItemsUseCase,
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
from tests.fakes.in_memory_shopping_list_item_repository import (
    InMemoryShoppingListItemRepository,
)
from tests.fakes.in_memory_substitution_repository import (
    InMemorySubstitutionRepository,
)
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"

USER_ID = "user-1"
RECIPE_ID = "recipe-pancakes"


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


def _inventory_item(ingredient_id: str) -> InventoryItem:
    return InventoryItem(
        id=f"item-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        quantity_state=QuantityState.IN,
        storage_location=StorageLocation.PANTRY,
        computed_freshness_date=datetime(2026, 1, 1, tzinfo=UTC).date(),
        freshness_date_type=FreshnessDateType.ESTIMATED_UNKNOWN,
        freshness_status=FreshnessDisplayStatus.FRESH,
        added_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id=RECIPE_ID,
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user() -> User:
    return User(
        id=USER_ID, hard_constraints=HardConstraints(), preferences=SoftPreferences()
    )


async def _build(
    recipes: list[Recipe], inventory_items: list[InventoryItem]
) -> tuple[AddShoppingListItemsUseCase, InMemoryShoppingListItemRepository]:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
    ]:
        await ingredient_repo.add(ingredient)

    recipe_repo = InMemoryRecipeRepository(recipes)
    substitution_repo = InMemorySubstitutionRepository([])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)
    user_repo = InMemoryUserRepository()
    await user_repo.add(_user())
    shopping_list_repo = InMemoryShoppingListItemRepository()

    use_case = AddShoppingListItemsUseCase(
        recipe_repository=recipe_repo,
        substitution_repository=substitution_repo,
        ingredient_repository=ingredient_repo,
        inventory_item_repository=inventory_repo,
        user_repository=user_repo,
        shopping_list_item_repository=shopping_list_repo,
    )
    return use_case, shopping_list_repo


@pytest.mark.asyncio
async def test_persists_one_item_per_true_gap() -> None:
    use_case, repo = await _build([_recipe()], [_inventory_item(FLOUR)])
    output = await use_case.execute(
        AddShoppingListItemsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )
    assert [i.ingredient_id for i in output.items] == [EGGS, MILK]

    persisted = await repo.list_by_user(USER_ID)
    assert {i.ingredient_id for i in persisted} == {EGGS, MILK}
    assert {i.recipe_id for i in persisted} == {RECIPE_ID}


@pytest.mark.asyncio
async def test_tapping_add_twice_does_not_duplicate_items() -> None:
    use_case, repo = await _build([_recipe()], [_inventory_item(FLOUR)])
    await use_case.execute(
        AddShoppingListItemsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )
    second_output = await use_case.execute(
        AddShoppingListItemsInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )

    assert second_output.items == []
    persisted = await repo.list_by_user(USER_ID)
    assert len(persisted) == 2


@pytest.mark.asyncio
async def test_unknown_recipe_raises_not_found() -> None:
    use_case, _ = await _build([], [])
    with pytest.raises(RecipeNotFoundError):
        await use_case.execute(
            AddShoppingListItemsInput(user_id=USER_ID, recipe_id="ghost-recipe")
        )


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case, _ = await _build([_recipe()], [])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            AddShoppingListItemsInput(user_id="ghost", recipe_id=RECIPE_ID)
        )
