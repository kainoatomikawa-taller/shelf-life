"""Unit tests for RecipeStockDecrementer (§5.6 AC2 — offer, don't force)."""

from datetime import UTC, datetime

from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.recipe import Recipe
from src.domain.services.recipe_stock_decrementer import RecipeStockDecrementer
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.storage_location import StorageLocation

USER_ID = "user-1"
FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
UNRELATED = "ingredient-unrelated"


def _recipe() -> Recipe:
    return Recipe(
        id="recipe-pancakes",
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.OPTIONAL),
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


def test_recipe_ingredients_in_stock_are_decrementable() -> None:
    decrementer = RecipeStockDecrementer()
    items = [
        _inventory_item(FLOUR, QuantityState.IN),
        _inventory_item(MILK, QuantityState.LOW),
    ]
    decrementable = decrementer.find_decrementable_items(_recipe(), items)
    assert {i.ingredient_id for i in decrementable} == {FLOUR, MILK}


def test_ingredients_already_out_are_excluded() -> None:
    decrementer = RecipeStockDecrementer()
    items = [_inventory_item(EGGS, QuantityState.OUT)]
    decrementable = decrementer.find_decrementable_items(_recipe(), items)
    assert decrementable == []


def test_ingredients_not_on_the_recipe_are_excluded() -> None:
    decrementer = RecipeStockDecrementer()
    items = [_inventory_item(UNRELATED, QuantityState.IN)]
    decrementable = decrementer.find_decrementable_items(_recipe(), items)
    assert decrementable == []
