"""FreshnessDateLabelResolver domain service.

Maps a FreshnessDateType to the exact label and tooltip subtext a user
should see, per spec section 4.3. Only the printed package date is worded
as definite; both estimate types say so plainly rather than borrowing the
authority of an "expiration" date they can't actually promise.
"""

from __future__ import annotations

from src.domain.value_objects.freshness_date_label import FreshnessDateLabel
from src.domain.value_objects.freshness_date_type import FreshnessDateType


class FreshnessDateLabelResolver:
    """Maps a freshness date's source signal to its display label."""

    _LABELS: dict[FreshnessDateType, FreshnessDateLabel] = {
        FreshnessDateType.PACKAGE: FreshnessDateLabel(
            label="Package use-by",
            tooltip="The use-by date printed on the package.",
        ),
        FreshnessDateType.ESTIMATED_FROM_PURCHASE: FreshnessDateLabel(
            label="Best used by (est.)",
            tooltip=(
                "Estimated from your purchase date and the typical shelf "
                "life for this food — not an exact date."
            ),
        ),
        FreshnessDateType.ESTIMATED_UNKNOWN: FreshnessDateLabel(
            label="Check by (est.)",
            tooltip=(
                "We don't know when you bought this, so this is a cautious "
                "guess — check the item before relying on it."
            ),
        ),
    }

    def resolve(self, date_type: FreshnessDateType) -> FreshnessDateLabel:
        return self._LABELS[date_type]
