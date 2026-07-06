"""Unit tests for FreshnessStatusResolver.derive_status."""

from datetime import date, timedelta

from src.domain.services.freshness_status_resolver import FreshnessStatusResolver
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.ingredient_category import IngredientCategory

TODAY = date(2026, 7, 6)


def _status(days_left: int, category: IngredientCategory) -> FreshnessDisplayStatus:
    computed_date = TODAY + timedelta(days=days_left)
    return FreshnessStatusResolver().derive_status(computed_date, TODAY, category)


def test_far_out_date_is_fresh() -> None:
    assert (
        _status(10, IngredientCategory.PERISHABLE_FRIDGE)
        == FreshnessDisplayStatus.FRESH
    )


def test_within_use_soon_window() -> None:
    assert (
        _status(2, IngredientCategory.PERISHABLE_FRIDGE)
        == FreshnessDisplayStatus.USE_SOON
    )


def test_within_use_now_window() -> None:
    assert (
        _status(0, IngredientCategory.PERISHABLE_FRIDGE)
        == FreshnessDisplayStatus.USE_NOW
    )


def test_past_computed_date_is_check_it_not_expired() -> None:
    status = _status(-1, IngredientCategory.PERISHABLE_FRIDGE)
    assert status == FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT


def test_thresholds_differ_by_category() -> None:
    # 10 days out is comfortably "fresh" for fridge perishables (3-day window)...
    assert (
        _status(10, IngredientCategory.PERISHABLE_FRIDGE)
        == FreshnessDisplayStatus.FRESH
    )
    # ...but already "use soon" for pantry goods, which get a longer heads-up
    # window (14 days) before their estimate.
    assert _status(10, IngredientCategory.PANTRY) == FreshnessDisplayStatus.USE_SOON


def test_spice_never_reaches_use_now() -> None:
    assert _status(0, IngredientCategory.SPICE) == FreshnessDisplayStatus.USE_SOON


def test_spice_never_reaches_past_estimate() -> None:
    assert (
        _status(-365, IngredientCategory.SPICE) == FreshnessDisplayStatus.USE_SOON
    )


def test_spice_can_still_be_fresh() -> None:
    assert _status(60, IngredientCategory.SPICE) == FreshnessDisplayStatus.FRESH
