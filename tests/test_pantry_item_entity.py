"""Unit tests for the PantryItem entity and freshness rules."""

from datetime import date, timedelta

import pytest

from src.domain.entities.pantry_item import FreshnessStatus, PantryItem
from src.domain.exceptions import ValidationError
from src.domain.value_objects.quantity import Quantity, Unit


def _item(exp_delta_days: int) -> PantryItem:
    return PantryItem(
        id="item-1",
        owner_id="user-1",
        name="Milk",
        quantity=Quantity(2, Unit.LITER),
        expiration_date=date.today() + timedelta(days=exp_delta_days),
    )


def test_fresh_item_is_fresh() -> None:
    assert _item(10).freshness_status(date.today()) == FreshnessStatus.FRESH


def test_item_expiring_soon() -> None:
    assert (
        _item(2).freshness_status(date.today())
        == FreshnessStatus.EXPIRING_SOON
    )


def test_expired_item() -> None:
    item = _item(-1)
    assert item.is_expired(date.today())
    assert item.freshness_status(date.today()) == FreshnessStatus.EXPIRED


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PantryItem(
            id="x",
            owner_id="u",
            name="   ",
            quantity=Quantity(1, Unit.PIECE),
            expiration_date=date.today(),
        )


def test_consume_reduces_quantity() -> None:
    item = _item(5)
    item.consume(Quantity(1, Unit.LITER))
    assert item.quantity.amount == 1


def test_consuming_more_than_available_raises() -> None:
    item = _item(5)
    with pytest.raises(ValidationError):
        item.consume(Quantity(99, Unit.LITER))
