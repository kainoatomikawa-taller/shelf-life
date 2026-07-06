"""Unit tests for the InventoryItem entity and its freshness engine integration."""

from datetime import date, datetime, timedelta, timezone

import pytest

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.inventory_item import InventoryItem
from src.domain.exceptions import ValidationError
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation

TODAY = date(2026, 7, 6)


def _ingredient(**overrides: object) -> Ingredient:
    defaults: dict = dict(
        id="ingredient-1",
        name="Milk",
        aliases=[],
        category=IngredientCategory.PERISHABLE_FRIDGE,
        default_storage_location=StorageLocation.FRIDGE,
        typical_shelf_life=ShelfLifeByStorage(fridge_days=7, freezer_days=90),
        allergen_tags=["dairy"],
        diet_tags=[],
    )
    defaults.update(overrides)
    return Ingredient(**defaults)  # type: ignore[arg-type]


def _item(**overrides: object) -> InventoryItem:
    defaults: dict = dict(
        id="item-1",
        user_id="user-1",
        ingredient=_ingredient(),
        quantity_state=QuantityState.IN,
        storage_location=StorageLocation.FRIDGE,
        added_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
        today=TODAY,
    )
    defaults.update(overrides)
    return InventoryItem.create(**defaults)  # type: ignore[arg-type]


def test_quantity_state_is_a_three_value_enum() -> None:
    assert {s.value for s in QuantityState} == {"in", "low", "out"}


def test_optional_date_fields_default_to_none() -> None:
    item = _item()
    assert item.purchase_date is None
    assert item.printed_package_date is None
    assert item.notes is None


def test_freshness_fields_are_populated_from_package_date() -> None:
    package_date = TODAY + timedelta(days=5)
    item = _item(printed_package_date=package_date)
    assert item.computed_freshness_date == package_date
    assert item.freshness_date_type == FreshnessDateType.PACKAGE
    assert item.freshness_status == FreshnessDisplayStatus.FRESH


def test_freshness_fields_are_populated_from_purchase_date() -> None:
    purchase_date = TODAY - timedelta(days=2)
    item = _item(purchase_date=purchase_date)
    assert item.computed_freshness_date == purchase_date + timedelta(days=7)
    assert item.freshness_date_type == FreshnessDateType.ESTIMATED_FROM_PURCHASE


def test_freshness_falls_back_to_caution_estimate_when_dates_unknown() -> None:
    item = _item()
    assert item.freshness_date_type == FreshnessDateType.ESTIMATED_UNKNOWN
    assert item.computed_freshness_date == TODAY + timedelta(days=4)  # 7 * 0.5, rounded


def test_frozen_item_uses_freezer_shelf_life() -> None:
    purchase_date = TODAY - timedelta(days=1)
    item = _item(
        storage_location=StorageLocation.FREEZER,
        is_frozen=True,
        purchase_date=purchase_date,
    )
    assert item.computed_freshness_date == purchase_date + timedelta(days=90)


def test_missing_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _item(id="")


def test_missing_user_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _item(user_id="")


def test_update_quantity_state() -> None:
    item = _item()
    item.update_quantity_state(QuantityState.LOW)
    assert item.quantity_state == QuantityState.LOW


def test_update_quantity_state_rejects_invalid_value() -> None:
    item = _item()
    with pytest.raises(ValidationError):
        item.update_quantity_state("low")  # type: ignore[arg-type]


def test_update_dates_recomputes_freshness_from_the_new_purchase_date() -> None:
    """§5.2 AC: the "edit dates" quick action corrects a wrong date."""
    item = _item()  # created with no purchase/package date known
    ingredient = _ingredient()
    corrected_purchase_date = TODAY - timedelta(days=2)

    item.update_dates(ingredient, TODAY, purchase_date=corrected_purchase_date)

    assert item.purchase_date == corrected_purchase_date
    assert item.computed_freshness_date == corrected_purchase_date + timedelta(days=7)
    assert item.freshness_date_type == FreshnessDateType.ESTIMATED_FROM_PURCHASE


def test_update_dates_can_clear_a_previously_set_date() -> None:
    package_date = TODAY + timedelta(days=5)
    item = _item(printed_package_date=package_date)
    ingredient = _ingredient()

    item.update_dates(ingredient, TODAY)

    assert item.printed_package_date is None
    assert item.freshness_date_type == FreshnessDateType.ESTIMATED_UNKNOWN


def test_move_storage_recomputes_freshness_for_new_location() -> None:
    purchase_date = TODAY - timedelta(days=1)
    item = _item(purchase_date=purchase_date)
    ingredient = _ingredient()

    item.move_storage(StorageLocation.FREEZER, ingredient, TODAY)

    assert item.storage_location == StorageLocation.FREEZER
    assert item.computed_freshness_date == purchase_date + timedelta(days=90)


def test_mark_thawed_pulls_freshness_date_earlier() -> None:
    ingredient = _ingredient(
        typical_shelf_life=ShelfLifeByStorage(fridge_days=7, freezer_days=90)
    )
    purchase_date = TODAY - timedelta(days=60)
    item = _item(
        ingredient=ingredient,
        storage_location=StorageLocation.FREEZER,
        is_frozen=True,
        purchase_date=purchase_date,
    )
    far_future_estimate = item.computed_freshness_date

    item.mark_thawed(thawed_at=TODAY, ingredient=ingredient, today=TODAY)

    assert item.is_frozen is False
    assert item.computed_freshness_date == TODAY + timedelta(days=3)
    assert item.computed_freshness_date < far_future_estimate
