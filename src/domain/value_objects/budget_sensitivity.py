"""BudgetSensitivity value object.

How strongly a user weighs ingredient/recipe cost when ranking recommendations.
Soft preference — never a hard eligibility filter.
"""

from __future__ import annotations

from enum import Enum


class BudgetSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
