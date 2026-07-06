"""FreshnessThresholds value object.

The day-count boundaries a category uses to separate Fresh / Use soon /
Use now, expressed as "days remaining until the computed freshness date".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FreshnessThresholds:
    use_soon_days: int
    use_now_days: int
