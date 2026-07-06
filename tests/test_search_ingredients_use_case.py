"""Use case tests for catalog search, using the in-memory repository."""

import pytest

from src.application.dtos.ingredient_dtos import SearchIngredientsInput
from src.application.use_cases.search_ingredients import SearchIngredientsUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository


async def _seeded_repo() -> InMemoryIngredientRepository:
    repo = InMemoryIngredientRepository()
    await repo.add(
        Ingredient(
            id="ingredient-green-onions",
            name="Green Onions",
            aliases=["scallion", "scallions", "spring onion"],
            category=IngredientCategory.PERISHABLE_FRIDGE,
            default_storage_location=StorageLocation.FRIDGE,
            typical_shelf_life=ShelfLifeByStorage(fridge_days=10),
            allergen_tags=[],
            diet_tags=[],
        )
    )
    await repo.add(
        Ingredient(
            id="ingredient-onions",
            name="Onions",
            aliases=["onion", "yellow onion"],
            category=IngredientCategory.PANTRY,
            default_storage_location=StorageLocation.PANTRY,
            typical_shelf_life=ShelfLifeByStorage(pantry_days=60),
            allergen_tags=[],
            diet_tags=[],
        )
    )
    return repo


@pytest.mark.asyncio
async def test_alias_search_resolves_to_canonical_ingredient() -> None:
    """§5.2 AC1: "scallion" search surfaces "Green Onions"."""
    use_case = SearchIngredientsUseCase(await _seeded_repo())

    results = await use_case.execute(SearchIngredientsInput(query="scallion"))

    assert [r.name for r in results] == ["Green Onions"]


@pytest.mark.asyncio
async def test_search_ranks_exact_alias_ahead_of_substring_matches() -> None:
    use_case = SearchIngredientsUseCase(await _seeded_repo())

    results = await use_case.execute(SearchIngredientsInput(query="onion"))

    assert [r.name for r in results] == ["Onions", "Green Onions"]


@pytest.mark.asyncio
async def test_blank_query_returns_no_results() -> None:
    use_case = SearchIngredientsUseCase(await _seeded_repo())

    results = await use_case.execute(SearchIngredientsInput(query="   "))

    assert results == []


@pytest.mark.asyncio
async def test_no_match_returns_empty_list() -> None:
    use_case = SearchIngredientsUseCase(await _seeded_repo())

    results = await use_case.execute(SearchIngredientsInput(query="garlic"))

    assert results == []
