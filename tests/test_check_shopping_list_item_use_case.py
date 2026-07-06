"""Use case tests for CheckShoppingListItem (§5.7 AC2 — check off as you shop)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.shopping_list_dtos import CheckShoppingListItemInput
from src.application.use_cases.check_shopping_list_item import (
    CheckShoppingListItemUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.exceptions import ShoppingListItemNotFoundError
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_shopping_list_item_repository import (
    InMemoryShoppingListItemRepository,
)

USER_ID = "user-1"
EGGS = "ingredient-eggs"
ITEM_ID = "sli-eggs"


async def _build() -> (
    tuple[CheckShoppingListItemUseCase, InMemoryShoppingListItemRepository]
):
    ingredient_repo = InMemoryIngredientRepository()
    await ingredient_repo.add(
        Ingredient(
            id=EGGS,
            name="Eggs",
            aliases=[],
            category=IngredientCategory.PANTRY,
            default_storage_location=StorageLocation.PANTRY,
            typical_shelf_life=ShelfLifeByStorage(pantry_days=30),
            allergen_tags=[],
            diet_tags=[],
        )
    )

    shopping_list_repo = InMemoryShoppingListItemRepository()
    await shopping_list_repo.add(
        ShoppingListItem(
            id=ITEM_ID,
            user_id=USER_ID,
            ingredient_id=EGGS,
            source_recipe_ids=["recipe-pancakes"],
            added_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
    )

    use_case = CheckShoppingListItemUseCase(shopping_list_repo, ingredient_repo)
    return use_case, shopping_list_repo


@pytest.mark.asyncio
async def test_checking_an_item_persists_checked_state() -> None:
    use_case, repo = await _build()
    output = await use_case.execute(
        CheckShoppingListItemInput(item_id=ITEM_ID, checked=True)
    )

    assert output.checked is True
    persisted = await repo.get_by_id(ITEM_ID)
    assert persisted is not None
    assert persisted.checked is True


@pytest.mark.asyncio
async def test_unchecking_a_checked_item() -> None:
    use_case, repo = await _build()
    await use_case.execute(CheckShoppingListItemInput(item_id=ITEM_ID, checked=True))
    output = await use_case.execute(
        CheckShoppingListItemInput(item_id=ITEM_ID, checked=False)
    )

    assert output.checked is False
    persisted = await repo.get_by_id(ITEM_ID)
    assert persisted is not None
    assert persisted.checked is False


@pytest.mark.asyncio
async def test_unknown_item_raises_not_found() -> None:
    use_case, _ = await _build()
    with pytest.raises(ShoppingListItemNotFoundError):
        await use_case.execute(
            CheckShoppingListItemInput(item_id="ghost", checked=True)
        )
