"""Use case tests for GetShoppingList (§5.7 AC1 — aggregation and merging)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.shopping_list_dtos import GetShoppingListInput
from src.application.use_cases.get_shopping_list import GetShoppingListUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)
from tests.fakes.in_memory_shopping_list_item_repository import (
    InMemoryShoppingListItemRepository,
)
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

USER_ID = "user-1"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
FLOUR = "ingredient-flour"


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


def _inventory_item(ingredient_id: str, quantity_state: QuantityState) -> InventoryItem:
    return InventoryItem(
        id=f"inv-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        quantity_state=quantity_state,
        storage_location=StorageLocation.PANTRY,
        computed_freshness_date=datetime(2026, 1, 1, tzinfo=UTC).date(),
        freshness_date_type=FreshnessDateType.ESTIMATED_UNKNOWN,
        freshness_status=FreshnessDisplayStatus.FRESH,
        added_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _explicit_item(ingredient_id: str, checked: bool = False) -> ShoppingListItem:
    return ShoppingListItem(
        id=f"sli-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        source_recipe_ids=["recipe-pancakes"],
        added_at=datetime(2026, 7, 1, tzinfo=UTC),
        checked=checked,
    )


async def _build(
    inventory_items: list[InventoryItem],
    explicit_items: list[ShoppingListItem],
) -> tuple[GetShoppingListUseCase, InMemoryShoppingListItemRepository]:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
        _ingredient(FLOUR, "Flour"),
    ]:
        await ingredient_repo.add(ingredient)

    inventory_repo = InMemoryInventoryItemRepository()
    for item in inventory_items:
        await inventory_repo.add(item)

    shopping_list_repo = InMemoryShoppingListItemRepository()
    for item in explicit_items:
        await shopping_list_repo.add(item)

    user_repo = InMemoryUserRepository()
    await user_repo.add(
        User(
            id=USER_ID,
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )
    )

    use_case = GetShoppingListUseCase(
        shopping_list_item_repository=shopping_list_repo,
        inventory_item_repository=inventory_repo,
        ingredient_repository=ingredient_repo,
        user_repository=user_repo,
    )
    return use_case, shopping_list_repo


@pytest.mark.asyncio
async def test_includes_explicit_discover_items() -> None:
    use_case, _ = await _build([], [_explicit_item(EGGS)])
    outputs = await use_case.execute(GetShoppingListInput(user_id=USER_ID))
    assert [o.ingredient_id for o in outputs] == [EGGS]


@pytest.mark.asyncio
async def test_low_and_out_inventory_flags_are_added_to_the_list() -> None:
    use_case, _ = await _build(
        [
            _inventory_item(MILK, QuantityState.LOW),
            _inventory_item(FLOUR, QuantityState.OUT),
            _inventory_item(EGGS, QuantityState.IN),
        ],
        [],
    )
    outputs = await use_case.execute(GetShoppingListInput(user_id=USER_ID))
    assert {o.ingredient_id for o in outputs} == {MILK, FLOUR}


@pytest.mark.asyncio
async def test_low_stock_flag_does_not_duplicate_an_existing_explicit_item() -> None:
    use_case, repo = await _build(
        [_inventory_item(EGGS, QuantityState.LOW)],
        [_explicit_item(EGGS)],
    )
    outputs = await use_case.execute(GetShoppingListInput(user_id=USER_ID))
    assert [o.ingredient_id for o in outputs] == [EGGS]
    assert len(await repo.list_by_user(USER_ID)) == 1


@pytest.mark.asyncio
async def test_low_stock_entries_persist_across_calls() -> None:
    use_case, repo = await _build([_inventory_item(MILK, QuantityState.LOW)], [])
    await use_case.execute(GetShoppingListInput(user_id=USER_ID))
    second = await use_case.execute(GetShoppingListInput(user_id=USER_ID))

    assert [o.ingredient_id for o in second] == [MILK]
    assert len(await repo.list_by_user(USER_ID)) == 1


@pytest.mark.asyncio
async def test_low_stock_entry_has_no_recipe_provenance_and_starts_unchecked() -> None:
    use_case, repo = await _build([_inventory_item(MILK, QuantityState.LOW)], [])
    outputs = await use_case.execute(GetShoppingListInput(user_id=USER_ID))

    assert outputs[0].checked is False
    persisted = await repo.list_by_user(USER_ID)
    assert persisted[0].source_recipe_ids == []


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case, _ = await _build([], [])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(GetShoppingListInput(user_id="ghost"))
