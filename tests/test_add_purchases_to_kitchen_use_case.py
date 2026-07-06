"""Use case tests for AddPurchasesToKitchen (§5.7 AC3 — loop-closer)."""

from datetime import UTC, date, datetime

import pytest

from src.application.dtos.shopping_list_dtos import AddPurchasesToKitchenInput
from src.application.use_cases.add_purchases_to_kitchen import (
    AddPurchasesToKitchenUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
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


def _item(ingredient_id: str, checked: bool) -> ShoppingListItem:
    return ShoppingListItem(
        id=f"sli-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        source_recipe_ids=["recipe-pancakes"],
        added_at=datetime(2026, 7, 1, tzinfo=UTC),
        checked=checked,
    )


async def _build(items: list[ShoppingListItem]) -> tuple[
    AddPurchasesToKitchenUseCase,
    InMemoryShoppingListItemRepository,
    InMemoryInventoryItemRepository,
]:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [_ingredient(EGGS, "Eggs"), _ingredient(MILK, "Milk")]:
        await ingredient_repo.add(ingredient)

    shopping_list_repo = InMemoryShoppingListItemRepository()
    for item in items:
        await shopping_list_repo.add(item)

    inventory_repo = InMemoryInventoryItemRepository()

    user_repo = InMemoryUserRepository()
    await user_repo.add(
        User(
            id=USER_ID,
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )
    )

    use_case = AddPurchasesToKitchenUseCase(
        shopping_list_item_repository=shopping_list_repo,
        inventory_item_repository=inventory_repo,
        ingredient_repository=ingredient_repo,
        user_repository=user_repo,
    )
    return use_case, shopping_list_repo, inventory_repo


@pytest.mark.asyncio
async def test_checked_items_become_inventory_items_dated_today() -> None:
    use_case, _, inventory_repo = await _build([_item(EGGS, checked=True)])
    outputs = await use_case.execute(AddPurchasesToKitchenInput(user_id=USER_ID))

    assert [o.ingredient_id for o in outputs] == [EGGS]
    assert outputs[0].purchase_date == date.today()

    persisted = await inventory_repo.list_by_user(USER_ID)
    assert len(persisted) == 1
    assert persisted[0].purchase_date == date.today()


@pytest.mark.asyncio
async def test_unchecked_items_are_left_on_the_shopping_list() -> None:
    use_case, shopping_list_repo, _ = await _build(
        [_item(EGGS, checked=True), _item(MILK, checked=False)]
    )
    await use_case.execute(AddPurchasesToKitchenInput(user_id=USER_ID))

    remaining = await shopping_list_repo.list_by_user(USER_ID)
    assert [i.ingredient_id for i in remaining] == [MILK]


@pytest.mark.asyncio
async def test_explicit_purchase_date_overrides_today() -> None:
    use_case, _, _ = await _build([_item(EGGS, checked=True)])
    chosen_date = date(2026, 6, 1)
    outputs = await use_case.execute(
        AddPurchasesToKitchenInput(user_id=USER_ID, purchase_date=chosen_date)
    )

    assert outputs[0].purchase_date == chosen_date


@pytest.mark.asyncio
async def test_no_checked_items_returns_empty_list() -> None:
    use_case, shopping_list_repo, _ = await _build([_item(EGGS, checked=False)])
    outputs = await use_case.execute(AddPurchasesToKitchenInput(user_id=USER_ID))

    assert outputs == []
    assert len(await shopping_list_repo.list_by_user(USER_ID)) == 1


@pytest.mark.asyncio
async def test_unknown_user_raises_not_found() -> None:
    use_case, _, _ = await _build([])
    with pytest.raises(UserNotFoundError):
        await use_case.execute(AddPurchasesToKitchenInput(user_id="ghost"))
