"""Unit tests for FreshnessDateLabelResolver.resolve."""

from src.domain.services.freshness_date_label_resolver import (
    FreshnessDateLabelResolver,
)
from src.domain.value_objects.freshness_date_type import FreshnessDateType

_ALL_LABELS = {
    date_type: FreshnessDateLabelResolver().resolve(date_type)
    for date_type in FreshnessDateType
}


def test_package_label_is_exact() -> None:
    label = FreshnessDateLabelResolver().resolve(FreshnessDateType.PACKAGE)
    assert label.label == "Package use-by"


def test_estimated_from_purchase_label_is_exact() -> None:
    label = FreshnessDateLabelResolver().resolve(
        FreshnessDateType.ESTIMATED_FROM_PURCHASE
    )
    assert label.label == "Best used by (est.)"


def test_estimated_unknown_label_is_exact() -> None:
    label = FreshnessDateLabelResolver().resolve(FreshnessDateType.ESTIMATED_UNKNOWN)
    assert label.label == "Check by (est.)"


def test_every_date_type_has_a_tooltip() -> None:
    for label in _ALL_LABELS.values():
        assert label.tooltip


def test_no_label_or_tooltip_says_expiration() -> None:
    for label in _ALL_LABELS.values():
        assert "expir" not in label.label.lower()
        assert "expir" not in label.tooltip.lower()
