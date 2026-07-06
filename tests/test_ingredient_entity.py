"""Unit tests for the Ingredient entity's catalog search behaviour."""

from src.domain.entities.ingredient import Ingredient
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation


def _green_onions() -> Ingredient:
    return Ingredient(
        id="ingredient-green-onions",
        name="Green Onions",
        aliases=["scallion", "scallions", "spring onion"],
        category=IngredientCategory.PERISHABLE_FRIDGE,
        default_storage_location=StorageLocation.FRIDGE,
        typical_shelf_life=ShelfLifeByStorage(fridge_days=10),
        allergen_tags=[],
        diet_tags=["vegan", "vegetarian"],
    )


def test_matches_query_resolves_alias() -> None:
    assert _green_onions().matches_query("scallion") is True
    assert _green_onions().matches_query("SCALLION") is True
    assert _green_onions().matches_query("shallot") is False


def test_search_rank_exact_alias_match_is_most_relevant() -> None:
    assert _green_onions().search_rank("scallion") == 0
    assert _green_onions().search_rank("Green Onions") == 0


def test_search_rank_prefix_match() -> None:
    assert _green_onions().search_rank("green") == 1
    assert _green_onions().search_rank("scal") == 1


def test_search_rank_substring_match() -> None:
    assert _green_onions().search_rank("onion") == 2


def test_search_rank_no_match_returns_none() -> None:
    assert _green_onions().search_rank("garlic") is None


def test_search_rank_blank_query_returns_none() -> None:
    assert _green_onions().search_rank("   ") is None


def test_add_alias_ignores_case_duplicate() -> None:
    ingredient = _green_onions()
    ingredient.add_alias("SCALLION")
    assert ingredient.aliases.count("scallion") + ingredient.aliases.count(
        "SCALLION"
    ) == 1
