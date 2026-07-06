"""FreshnessCalculator domain service.

Resolves a pantry item's freshness date from the most credible signal
available, in priority order: a printed package date, then an estimate
anchored to a known purchase date, then a conservative estimate when even
the purchase date is unknown. Freezing pauses/extends the clock by pricing
shelf life at the freezer rate; thawing opens a short, independent
food-safety window that can only pull the resolved date earlier, never
push it later.
"""

from __future__ import annotations

from datetime import date, timedelta

from src.domain.exceptions import ValidationError
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_input import FreshnessInput
from src.domain.value_objects.freshness_result import FreshnessResult


class FreshnessCalculator:
    """Computes a pantry item's freshness date from available signals."""

    # Fraction of typical shelf life trusted when the purchase date is
    # unknown. The single tunable knob for how conservative that guess is.
    CAUTION_FACTOR = 0.5

    # Food-safety window after an item thaws, independent of how long it
    # would otherwise be considered good.
    THAW_SAFETY_WINDOW_DAYS = 3

    def compute_freshness(self, item: FreshnessInput, today: date) -> FreshnessResult:
        """Pick the soonest credible freshness date, by priority."""
        if item.package_date is not None:
            return FreshnessResult(item.package_date, FreshnessDateType.PACKAGE)

        shelf_life_days = (
            item.freezer_shelf_life_days
            if item.is_frozen
            else item.storage_shelf_life_days
        )
        if shelf_life_days is None:
            raise ValidationError(
                "Cannot compute freshness without a package date or a known "
                "shelf life for the item's current storage state."
            )

        if item.purchase_date is not None:
            freshness_date = item.purchase_date + timedelta(days=shelf_life_days)
            date_type = FreshnessDateType.ESTIMATED_FROM_PURCHASE
        else:
            caution_days = round(shelf_life_days * self.CAUTION_FACTOR)
            freshness_date = today + timedelta(days=caution_days)
            date_type = FreshnessDateType.ESTIMATED_UNKNOWN

        if item.thawed_at is not None:
            thaw_deadline = item.thawed_at + timedelta(
                days=self.THAW_SAFETY_WINDOW_DAYS
            )
            freshness_date = min(freshness_date, thaw_deadline)

        return FreshnessResult(freshness_date, date_type)
