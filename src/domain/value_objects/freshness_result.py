"""FreshnessResult value object.

The output of computeFreshness: the resolved freshness date and which
signal it was derived from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.value_objects.freshness_date_type import FreshnessDateType


@dataclass(frozen=True)
class FreshnessResult:
    freshness_date: date
    freshness_date_type: FreshnessDateType
