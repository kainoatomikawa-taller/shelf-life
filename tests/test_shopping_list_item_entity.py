"""Unit tests for the ShoppingListItem entity's invariants (§8)."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.exceptions import ValidationError
from src.domain.value_objects.quantity import Quantity, Unit


def _item(**overrides: object) -> ShoppingListItem:
    defaults: dict = dict(
        id="item-1",
        user_id="user-1",
        ingredient_id="ingredient-eggs",
        source_recipe_ids=["recipe-pancakes"],
        added_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    defaults.update(overrides)
    return ShoppingListItem(**defaults)  # type: ignore[arg-type]


def test_defaults_to_unchecked_with_no_quantity() -> None:
    item = _item()
    assert item.checked is False
    assert item.quantity_needed is None
    assert item.source_recipe_ids == ["recipe-pancakes"]


def test_tracks_quantity_needed_and_checked_state() -> None:
    quantity = Quantity(amount=2, unit=Unit.PIECE)
    item = _item(checked=True, quantity_needed=quantity)
    assert item.checked is True
    assert item.quantity_needed == quantity


def test_add_source_recipe_is_idempotent() -> None:
    item = _item(source_recipe_ids=["recipe-pancakes"])
    item.add_source_recipe("recipe-waffles")
    item.add_source_recipe("recipe-waffles")
    assert item.source_recipe_ids == ["recipe-pancakes", "recipe-waffles"]


def test_mark_checked_and_unchecked() -> None:
    item = _item()
    item.mark_checked()
    assert item.checked is True
    item.mark_unchecked()
    assert item.checked is False


def test_rejects_empty_source_recipe_ids() -> None:
    with pytest.raises(ValidationError):
        _item(source_recipe_ids=[])


def test_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        _item(id="")
    with pytest.raises(ValidationError):
        _item(user_id="")
    with pytest.raises(ValidationError):
        _item(ingredient_id="")
