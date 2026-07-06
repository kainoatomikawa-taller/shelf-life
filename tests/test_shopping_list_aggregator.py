"""Unit tests for ShoppingListAggregator (§5.7 AC1 — merges duplicates)."""

from datetime import UTC, datetime

from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.services.shopping_list_aggregator import ShoppingListAggregator

USER_ID = "user-1"


def _existing_item(ingredient_id: str) -> ShoppingListItem:
    return ShoppingListItem(
        id=f"item-{ingredient_id}",
        user_id=USER_ID,
        ingredient_id=ingredient_id,
        source_recipe_ids=["recipe-pancakes"],
        added_at=datetime(2026, 7, 6, tzinfo=UTC),
    )


def test_low_stock_ingredient_not_on_list_is_missing() -> None:
    aggregator = ShoppingListAggregator()
    missing = aggregator.missing_low_stock_entries([], ["ingredient-eggs"])
    assert missing == ["ingredient-eggs"]


def test_low_stock_ingredient_already_on_list_is_not_duplicated() -> None:
    aggregator = ShoppingListAggregator()
    existing = [_existing_item("ingredient-eggs")]
    missing = aggregator.missing_low_stock_entries(
        existing, ["ingredient-eggs", "ingredient-milk"]
    )
    assert missing == ["ingredient-milk"]


def test_low_stock_ids_are_deduplicated_among_themselves() -> None:
    aggregator = ShoppingListAggregator()
    missing = aggregator.missing_low_stock_entries(
        [], ["ingredient-eggs", "ingredient-eggs"]
    )
    assert missing == ["ingredient-eggs"]


def test_no_missing_entries_when_everything_is_already_listed() -> None:
    aggregator = ShoppingListAggregator()
    existing = [_existing_item("ingredient-eggs")]
    missing = aggregator.missing_low_stock_entries(existing, ["ingredient-eggs"])
    assert missing == []
