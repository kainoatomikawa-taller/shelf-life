"""FreshnessDisplayStatus value object.

The four freshness states shown to a user, derived from how a computed
freshness date compares to today. "Past estimate" is deliberately worded as
an advisory to go check the item, not an automatic instruction to discard it.
"""

from __future__ import annotations

from enum import Enum


class FreshnessDisplayStatus(str, Enum):
    FRESH = "fresh"
    USE_SOON = "use_soon"
    USE_NOW = "use_now"
    PAST_ESTIMATE_CHECK_IT = "past_estimate_check_it"
