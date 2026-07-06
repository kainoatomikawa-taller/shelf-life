"""Unit tests for FreshnessPresenter.present."""

from src.domain.services.freshness_presenter import FreshnessPresenter
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.ingredient_category import IngredientCategory


def test_fresh_item_has_no_spoilage_check_tip() -> None:
    display = FreshnessPresenter().present(
        FreshnessDateType.ESTIMATED_FROM_PURCHASE,
        FreshnessDisplayStatus.FRESH,
        IngredientCategory.PERISHABLE_FRIDGE,
    )
    assert display.spoilage_check_tip is None


def test_use_soon_item_has_no_spoilage_check_tip() -> None:
    display = FreshnessPresenter().present(
        FreshnessDateType.PACKAGE,
        FreshnessDisplayStatus.USE_SOON,
        IngredientCategory.PANTRY,
    )
    assert display.spoilage_check_tip is None


def test_past_estimate_item_surfaces_a_spoilage_check_tip() -> None:
    display = FreshnessPresenter().present(
        FreshnessDateType.ESTIMATED_UNKNOWN,
        FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT,
        IngredientCategory.PERISHABLE_COUNTER,
    )
    assert display.spoilage_check_tip is not None
    assert display.spoilage_check_tip.smell


def test_past_estimate_tip_matches_ingredient_category() -> None:
    display = FreshnessPresenter().present(
        FreshnessDateType.ESTIMATED_UNKNOWN,
        FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT,
        IngredientCategory.FROZEN,
    )
    assert "thaw" in display.spoilage_check_tip.smell.lower()


def test_date_label_reflects_the_date_type() -> None:
    display = FreshnessPresenter().present(
        FreshnessDateType.PACKAGE,
        FreshnessDisplayStatus.FRESH,
        IngredientCategory.PERISHABLE_FRIDGE,
    )
    assert display.date_label.label == "Package use-by"
