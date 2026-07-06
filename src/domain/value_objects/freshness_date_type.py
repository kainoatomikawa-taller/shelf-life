"""FreshnessDateType value object.

Identifies which signal computeFreshness resolved a pantry item's freshness
date from, in descending order of trustworthiness: an explicit printed
package date, an estimate anchored to a known purchase date, or a
conservative estimate when even the purchase date is unknown.
"""

from __future__ import annotations

from enum import Enum


class FreshnessDateType(str, Enum):
    PACKAGE = "package"
    ESTIMATED_FROM_PURCHASE = "est-from-purchase"
    ESTIMATED_UNKNOWN = "est-unknown"
