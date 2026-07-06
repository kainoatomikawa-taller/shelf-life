"""FreshnessPresenter domain service.

Composes the date-type label and the spoilage-check guidance into the
single bundle a UI renders for a pantry item's freshness date. Keeping the
composition here — rather than in each caller — is what guarantees the
spoilage-check tip only ever appears alongside "past estimate — check it".
"""

from __future__ import annotations

from src.domain.services.freshness_date_label_resolver import (
    FreshnessDateLabelResolver,
)
from src.domain.services.spoilage_check_guidance_resolver import (
    SpoilageCheckGuidanceResolver,
)
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display import FreshnessDisplay
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.ingredient_category import IngredientCategory


class FreshnessPresenter:
    """Builds the display bundle for a pantry item's freshness date."""

    def __init__(
        self,
        date_label_resolver: FreshnessDateLabelResolver | None = None,
        spoilage_check_guidance_resolver: SpoilageCheckGuidanceResolver | None = None,
    ) -> None:
        self._date_label_resolver = date_label_resolver or FreshnessDateLabelResolver()
        self._spoilage_check_guidance_resolver = (
            spoilage_check_guidance_resolver or SpoilageCheckGuidanceResolver()
        )

    def present(
        self,
        date_type: FreshnessDateType,
        status: FreshnessDisplayStatus,
        category: IngredientCategory,
    ) -> FreshnessDisplay:
        spoilage_check_tip = (
            self._spoilage_check_guidance_resolver.resolve(category)
            if status == FreshnessDisplayStatus.PAST_ESTIMATE_CHECK_IT
            else None
        )
        return FreshnessDisplay(
            date_label=self._date_label_resolver.resolve(date_type),
            status=status,
            spoilage_check_tip=spoilage_check_tip,
        )
