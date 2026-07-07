"""Use case tests for GenerateShoppingListForRecipe (§5.4 AC3)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.discover_dtos import GenerateShoppingListInput
from src.application.use_cases.generate_shopping_list_for_recipe import (
    GenerateShoppingListForRecipeUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
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


def _inventory_item(
    ingredient_id: str, quantity_state: QuantityState = QuantityState.IN
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
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user() -> User:
    return User(
        id=USER_ID, hard_constraints=HardConstraints(), preferences=SoftPreferences()
    )


async def _build_use_case(
    recipes: list[Recipe],
    inventory_items: list[InventoryItem],
    substitutions: list[Substitution] | None = None,
) -> GenerateShoppingListForRecipeUseCase:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
        _ingredient(ALMOND_MILK, "Almond Milk"),
    ]:
        await ingredient_repo.add(ingredient)

    recipe_repo = InMemoryRecipeRepository(recipes)
    substitution_repo = InMemorySubstitutionRepository(substitutions or [])
    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)
    user_repo = InMemoryUserRepository()
    await user_repo.add(_user())

    return GenerateShoppingListForRecipeUseCase(
        recipe_repository=recipe_repo,
        substitution_repository=substitution_repo,
        ingredient_repository=ingredient_repo,
        inventory_item_repository=inventory_repo,
        user_repository=user_repo,
    )


@pytest.mark.asyncio
async def test_generates_only_true_gaps() -> None:
    use_case = await _build_use_case([_recipe()], [_inventory_item(FLOUR)])
    output = await use_case.execute(
        GenerateShoppingListInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )
    assert [i.ingredient_id for i in output.items] == [EGGS, MILK]
    assert [i.ingredient_name for i in output.items] == ["Eggs", "Milk"]


@pytest.mark.asyncio
async def test_excludes_essential_covered_by_valid_substitution() -> None:
    substitution = Substitution(
        id="sub-1",
        from_ingredient_id=MILK,
        to_ingredient_id=ALMOND_MILK,
        context=SubstitutionContext.GENERAL,
        confidence=0.9,
    )
    use_case = await _build_use_case(
        [_recipe()],
        [_inventory_item(FLOUR), _inventory_item(EGGS), _inventory_item(ALMOND_MILK)],
        substitutions=[substitution],
    )
    output = await use_case.execute(
        GenerateShoppingListInput(user_id=USER_ID, recipe_id=RECIPE_ID)
    )
    assert output.items == []


@pytest.mark.asyncio
async def test_unknown_recipe_raises_not_found() -> None:
    use_case = await _build_use_case([], [])
    with pytest.raises(RecipeNotFoundError):
        await use_case.execute(
            GenerateShoppingListInput(user_id=USER_ID, recipe_id="ghost-recipe")
        )


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case = await _build_use_case([_recipe()], [])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            GenerateShoppingListInput(user_id="ghost", recipe_id=RECIPE_ID)
        )
