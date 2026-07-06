"""FreshnessDateLabel value object.

The user-facing label and tooltip subtext for a freshness date, chosen
based on how trustworthy the underlying signal is. Wording is deliberately
never "expiration" — every non-package date is an estimate, and saying
otherwise overstates certainty the app doesn't have.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FreshnessDateLabel:
    label: str
    tooltip: str
