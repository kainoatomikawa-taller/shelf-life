"""Use case tests for the Kitchen list's per-item quick actions (§5.2 AC2):
one-tap Mark Low / Mark Out, edit dates, and used-it-up / delete.
"""

from datetime import date, timedelta

import pytest

from src.application.dtos.inventory_item_dtos import (
    AddInventoryItemInput,
    RemoveInventoryItemInput,
    UpdateInventoryItemDatesInput,
    UpdateQuantityStateInput,
)
from src.application.use_cases.add_inventory_item import AddInventoryItemUseCase
from src.application.use_cases.remove_inventory_item import RemoveInventoryItemUseCase
from src.application.use_cases.update_inventory_item_dates import (
    UpdateInventoryItemDatesUseCase,
)
from src.application.use_cases.update_inventory_item_quantity_state import (
    UpdateInventoryItemQuantityStateUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.exceptions import InventoryItemNotFoundError
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)


async def _add_milk_item() -> tuple[
    str, InMemoryInventoryItemRepository, InMemoryIngredientRepository
]:
    ingredient_repo = InMemoryIngredientRepository()
    await ingredient_repo.add(
        Ingredient(
            id="ingredient-milk",
            name="Milk",
            aliases=[],
            category=IngredientCategory.PERISHABLE_FRIDGE,
            default_storage_location=StorageLocation.FRIDGE,
            typical_shelf_life=ShelfLifeByStorage(fridge_days=7, freezer_days=90),
            allergen_tags=["dairy"],
            diet_tags=[],
        )
    )
    inventory_repo = InMemoryInventoryItemRepository()
    add_use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)
    output = await add_use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )
    return output.id, inventory_repo, ingredient_repo


@pytest.mark.asyncio
async def test_mark_low_updates_quantity_state() -> None:
    item_id, inventory_repo, ingredient_repo = await _add_milk_item()
    use_case = UpdateInventoryItemQuantityStateUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        UpdateQuantityStateInput(item_id=item_id, quantity_state="low")
    )

    assert output.quantity_state == "low"
    persisted = await inventory_repo.get_by_id(item_id)
    assert persisted is not None
    assert persisted.quantity_state.value == "low"


@pytest.mark.asyncio
async def test_mark_out_updates_quantity_state() -> None:
    item_id, inventory_repo, ingredient_repo = await _add_milk_item()
    use_case = UpdateInventoryItemQuantityStateUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        UpdateQuantityStateInput(item_id=item_id, quantity_state="out")
    )

    assert output.quantity_state == "out"


@pytest.mark.asyncio
async def test_quantity_state_update_on_missing_item_raises() -> None:
    _, inventory_repo, ingredient_repo = await _add_milk_item()
    use_case = UpdateInventoryItemQuantityStateUseCase(inventory_repo, ingredient_repo)

    with pytest.raises(InventoryItemNotFoundError):
        await use_case.execute(
            UpdateQuantityStateInput(item_id="does-not-exist", quantity_state="low")
        )


@pytest.mark.asyncio
async def test_edit_dates_recomputes_the_labeled_freshness_date() -> None:
    item_id, inventory_repo, ingredient_repo = await _add_milk_item()
    use_case = UpdateInventoryItemDatesUseCase(inventory_repo, ingredient_repo)
    corrected_purchase_date = date.today() - timedelta(days=1)

    output = await use_case.execute(
        UpdateInventoryItemDatesInput(
            item_id=item_id, purchase_date=corrected_purchase_date
        )
    )

    assert output.purchase_date == corrected_purchase_date
    assert output.computed_freshness_date == corrected_purchase_date + timedelta(
        days=7
    )
    assert output.freshness_date_type == "est-from-purchase"
    assert output.freshness_date_label == "Best used by (est.)"


@pytest.mark.asyncio
async def test_edit_dates_on_missing_item_raises() -> None:
    _, inventory_repo, ingredient_repo = await _add_milk_item()
    use_case = UpdateInventoryItemDatesUseCase(inventory_repo, ingredient_repo)

    with pytest.raises(InventoryItemNotFoundError):
        await use_case.execute(
            UpdateInventoryItemDatesInput(item_id="does-not-exist")
        )


@pytest.mark.asyncio
async def test_used_it_up_removes_the_item() -> None:
    item_id, inventory_repo, _ = await _add_milk_item()
    use_case = RemoveInventoryItemUseCase(inventory_repo)

    await use_case.execute(RemoveInventoryItemInput(item_id=item_id))

    assert await inventory_repo.get_by_id(item_id) is None


@pytest.mark.asyncio
async def test_removing_a_missing_item_raises() -> None:
    _, inventory_repo, _ = await _add_milk_item()
    use_case = RemoveInventoryItemUseCase(inventory_repo)

    with pytest.raises(InventoryItemNotFoundError):
        await use_case.execute(RemoveInventoryItemInput(item_id="does-not-exist"))
