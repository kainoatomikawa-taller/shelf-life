"""Use case tests for adding inventory items, using in-memory repositories."""

from datetime import date, timedelta

import pytest

from src.application.dtos.inventory_item_dtos import AddInventoryItemInput
from src.application.use_cases.add_inventory_item import AddInventoryItemUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.exceptions import IngredientNotFoundError
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_inventory_item_repository import (
    InMemoryInventoryItemRepository,
)


async def _repos_with_milk() -> tuple[
    InMemoryInventoryItemRepository, InMemoryIngredientRepository
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
    return InMemoryInventoryItemRepository(), ingredient_repo


@pytest.mark.asyncio
async def test_only_ingredient_is_required() -> None:
    """§5.2 AC2: every field but the ingredient is skippable."""
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )

    assert output.ingredient_id == "ingredient-milk"
    assert len(await inventory_repo.list_by_user("user-1")) == 1


@pytest.mark.asyncio
async def test_storage_location_defaults_from_ingredient_category() -> None:
    """§5.2 AC3: category auto-suggests storage location."""
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )

    assert output.storage_location == "fridge"


@pytest.mark.asyncio
async def test_quantity_state_defaults_to_in() -> None:
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )

    assert output.quantity_state == "in"


@pytest.mark.asyncio
async def test_shelf_life_is_derived_from_category_when_dates_are_skipped() -> None:
    """§5.2 AC3: category auto-suggests shelf life via the freshness engine."""
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )

    assert output.computed_freshness_date == date.today() + timedelta(days=4)
    assert output.freshness_date_type == "est-unknown"


@pytest.mark.asyncio
async def test_output_carries_the_labeled_freshness_date() -> None:
    """Kitchen list AC1: rows show the correct labeled freshness date."""
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(user_id="user-1", ingredient_id="ingredient-milk")
    )

    assert output.freshness_date_label == "Check by (est.)"
    assert "cautious guess" in output.freshness_date_tooltip
    assert output.ingredient_category == "perishable_fridge"
    assert output.spoilage_check_tip is None


@pytest.mark.asyncio
async def test_explicit_storage_location_overrides_the_default() -> None:
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    output = await use_case.execute(
        AddInventoryItemInput(
            user_id="user-1",
            ingredient_id="ingredient-milk",
            storage_location="freezer",
            is_frozen=True,
        )
    )

    assert output.storage_location == "freezer"


@pytest.mark.asyncio
async def test_unknown_ingredient_raises() -> None:
    inventory_repo, ingredient_repo = await _repos_with_milk()
    use_case = AddInventoryItemUseCase(inventory_repo, ingredient_repo)

    with pytest.raises(IngredientNotFoundError):
        await use_case.execute(
            AddInventoryItemInput(user_id="user-1", ingredient_id="does-not-exist")
        )
