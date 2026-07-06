"""ExpirationService domain service.

Encapsulates business logic that spans a collection of pantry items, such as
selecting which items need attention. Pure logic, no I/O.
"""

from __future__ import annotations

from datetime import date

from src.domain.entities.pantry_item import FreshnessStatus, PantryItem


class ExpirationService:
    """Business rules over a collection of pantry items."""

    def items_needing_attention(
        self, items: list[PantryItem], today: date
    ) -> list[PantryItem]:
        """Return items that are expired or expiring soon, most urgent first."""
        flagged = [
            item
            for item in items
            if item.freshness_status(today)
            in (FreshnessStatus.EXPIRED, FreshnessStatus.EXPIRING_SOON)
        ]
        return sorted(flagged, key=lambda item: item.expiration_date)

    def count_by_status(
        self, items: list[PantryItem], today: date
    ) -> dict[str, int]:
        """Return a count of items grouped by freshness status."""
        counts = {
            FreshnessStatus.FRESH: 0,
            FreshnessStatus.EXPIRING_SOON: 0,
            FreshnessStatus.EXPIRED: 0,
        }
        for item in items:
            counts[item.freshness_status(today)] += 1
        return counts
