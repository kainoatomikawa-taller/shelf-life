"""FreshnessDisplay value object.

Everything a UI needs to render a pantry item's freshness date: the label
and tooltip for its date type, its display status, and — only once the
estimate has passed — a spoilage-check tip so "past estimate" reads as
"go check it" rather than "throw it out".
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.freshness_date_label import FreshnessDateLabel
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.spoilage_check_tip import SpoilageCheckTip


@dataclass(frozen=True)
class FreshnessDisplay:
    date_label: FreshnessDateLabel
    status: FreshnessDisplayStatus
    spoilage_check_tip: SpoilageCheckTip | None
