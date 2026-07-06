"""Unit tests for FreshnessCalculator.compute_freshness."""

from datetime import date, timedelta

import pytest

from src.domain.exceptions import ValidationError
from src.domain.services.freshness_calculator import FreshnessCalculator
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_input import FreshnessInput

TODAY = date(2026, 7, 6)


def _input(**overrides: object) -> FreshnessInput:
    defaults: dict[str, object] = {
        "package_date": None,
        "purchase_date": None,
        "storage_shelf_life_days": 10,
        "freezer_shelf_life_days": 90,
        "is_frozen": False,
        "thawed_at": None,
    }
    defaults.update(overrides)
    return FreshnessInput(**defaults)  # type: ignore[arg-type]


def test_package_date_always_wins() -> None:
    package_date = TODAY + timedelta(days=30)
    item = _input(
        package_date=package_date,
        purchase_date=TODAY - timedelta(days=2),
    )
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    assert result.freshness_date == package_date
    assert result.freshness_date_type == FreshnessDateType.PACKAGE


def test_purchase_date_plus_storage_shelf_life() -> None:
    purchase_date = TODAY - timedelta(days=2)
    item = _input(purchase_date=purchase_date, storage_shelf_life_days=10)
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    assert result.freshness_date == purchase_date + timedelta(days=10)
    assert result.freshness_date_type == FreshnessDateType.ESTIMATED_FROM_PURCHASE


def test_unknown_purchase_date_uses_caution_factor() -> None:
    item = _input(storage_shelf_life_days=10)
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    expected_days = round(10 * FreshnessCalculator.CAUTION_FACTOR)
    assert result.freshness_date == TODAY + timedelta(days=expected_days)
    assert result.freshness_date_type == FreshnessDateType.ESTIMATED_UNKNOWN


def test_frozen_item_uses_freezer_shelf_life() -> None:
    purchase_date = TODAY - timedelta(days=5)
    item = _input(
        purchase_date=purchase_date,
        storage_shelf_life_days=10,
        freezer_shelf_life_days=90,
        is_frozen=True,
    )
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    assert result.freshness_date == purchase_date + timedelta(days=90)
    assert result.freshness_date_type == FreshnessDateType.ESTIMATED_FROM_PURCHASE


def test_thawing_restarts_a_short_countdown() -> None:
    purchase_date = TODAY - timedelta(days=5)
    thawed_at = TODAY - timedelta(days=1)
    item = _input(
        purchase_date=purchase_date,
        freezer_shelf_life_days=90,
        is_frozen=False,
        thawed_at=thawed_at,
    )
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    expected = thawed_at + timedelta(days=FreshnessCalculator.THAW_SAFETY_WINDOW_DAYS)
    assert result.freshness_date == expected


def test_thaw_deadline_only_shortens_never_extends() -> None:
    purchase_date = TODAY - timedelta(days=1)
    thawed_at = TODAY - timedelta(days=1)
    item = _input(
        purchase_date=purchase_date,
        storage_shelf_life_days=1,
        thawed_at=thawed_at,
    )
    result = FreshnessCalculator().compute_freshness(item, TODAY)
    naive_estimate = purchase_date + timedelta(days=1)
    assert result.freshness_date == min(
        naive_estimate,
        thawed_at + timedelta(days=FreshnessCalculator.THAW_SAFETY_WINDOW_DAYS),
    )


def test_missing_shelf_life_without_package_date_raises() -> None:
    item = _input(storage_shelf_life_days=None, freezer_shelf_life_days=None)
    with pytest.raises(ValidationError):
        FreshnessCalculator().compute_freshness(item, TODAY)
