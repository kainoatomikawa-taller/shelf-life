"""PantryItem entity.

Represents a single food item stored in a user's pantry. The entity owns
its invariants and freshness logic. It has no knowledge of persistence,
transport or frameworks.
"""

from __future__ import annotations

from datetime import date

from src.domain.exceptions import ValidationError
from src.domain.value_objects.quantity import Quantity


class FreshnessStatus:
    """Named freshness states for a pantry item."""

    FRESH = "fresh"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"


class PantryItem:
    """A food item with identity, quantity and an expiration date."""

    # Number of days before expiry at which an item counts as "expiring soon".
    EXPIRING_SOON_THRESHOLD_DAYS = 3

    def __init__(
        self,
        id: str,
        owner_id: str,
        name: str,
        quantity: Quantity,
        expiration_date: date,
    ) -> None:
        if not id:
            raise ValidationError("PantryItem id is required.")
        if not owner_id:
            raise ValidationError("PantryItem owner_id is required.")
        if not name or not name.strip():
            raise ValidationError("PantryItem name cannot be empty.")

        self._id = id
        self._owner_id = owner_id
        self._name = name.strip()
        self._quantity = quantity
        self._expiration_date = expiration_date

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def owner_id(self) -> str:
        return self._owner_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @property
    def expiration_date(self) -> date:
        return self._expiration_date

    # --- Behaviour (business rules live here) -------------------------------

    def days_until_expiration(self, today: date) -> int:
        """Whole days between today and the expiration date (may be negative)."""
        return (self._expiration_date - today).days

    def freshness_status(self, today: date) -> str:
        """Compute the freshness state relative to a reference date."""
        days_left = self.days_until_expiration(today)
        if days_left < 0:
            return FreshnessStatus.EXPIRED
        if days_left <= self.EXPIRING_SOON_THRESHOLD_DAYS:
            return FreshnessStatus.EXPIRING_SOON
        return FreshnessStatus.FRESH

    def is_expired(self, today: date) -> bool:
        return self.freshness_status(today) == FreshnessStatus.EXPIRED

    def consume(self, amount: Quantity) -> None:
        """Reduce the stored quantity by the given amount."""
        self._quantity = self._quantity.subtract(amount)

    def restock(self, amount: Quantity) -> None:
        """Increase the stored quantity by the given amount."""
        self._quantity = self._quantity.add(amount)

    def rename(self, new_name: str) -> None:
        if not new_name or not new_name.strip():
            raise ValidationError("PantryItem name cannot be empty.")
        self._name = new_name.strip()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PantryItem):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
