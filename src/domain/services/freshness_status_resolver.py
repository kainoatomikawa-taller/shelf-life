"""FreshnessStatusResolver domain service.

Derives a user-facing freshness status from a computed freshness date by
comparing days-remaining against category-specific thresholds. Spices lose
potency rather than spoil, so they're capped at a soft "use soon" nudge and
never escalate to the more alarming "use now" or "past estimate" states.
"""

from __future__ import annotations

from datetime import date

from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.freshness_thresholds import FreshnessThresholds
from src.domain.value_objects.ingredient_category import IngredientCategory

# Display states a spice may never reach — potency loss is a soft nudge,
# never a food-safety "toss it" alarm.
_ALARM_STATUSES = (
    FreshnessDisplayStatus.USE_NOW,
    FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT,
)


class FreshnessStatusResolver:
    """Maps a computed freshness date to a user-facing display status."""

    DEFAULT_THRESHOLDS = FreshnessThresholds(use_soon_days=3, use_now_days=0)

    CATEGORY_THRESHOLDS: dict[IngredientCategory, FreshnessThresholds] = {
        IngredientCategory.PERISHABLE_FRIDGE: FreshnessThresholds(
            use_soon_days=3, use_now_days=0
        ),
        IngredientCategory.PERISHABLE_COUNTER: FreshnessThresholds(
            use_soon_days=2, use_now_days=0
        ),
        IngredientCategory.FROZEN: FreshnessThresholds(
            use_soon_days=7, use_now_days=1
        ),
        IngredientCategory.PANTRY: FreshnessThresholds(
            use_soon_days=14, use_now_days=3
        ),
        IngredientCategory.SPICE: FreshnessThresholds(
            use_soon_days=30, use_now_days=0
        ),
    }

    def derive_status(
        self, computed_date: date, today: date, category: IngredientCategory
    ) -> FreshnessDisplayStatus:
        thresholds = self.CATEGORY_THRESHOLDS.get(category, self.DEFAULT_THRESHOLDS)
        days_left = (computed_date - today).days

        if days_left > thresholds.use_soon_days:
            status = FreshnessDisplayStatus.FRESH
        elif days_left > thresholds.use_now_days:
            status = FreshnessDisplayStatus.USE_SOON
        elif days_left >= 0:
            status = FreshnessDisplayStatus.USE_NOW
        else:
            status = FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT

        if category == IngredientCategory.SPICE and status in _ALARM_STATUSES:
            return FreshnessDisplayStatus.USE_SOON

        return status
