"""Quantity value object.

Immutable representation of an amount of a pantry item together with its
unit of measure. Equality is by value, and invariants are protected in the
constructor.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.exceptions import ValidationError


class Unit(str, Enum):
    """Supported units of measure for pantry items."""

    PIECE = "piece"
    GRAM = "gram"
    KILOGRAM = "kilogram"
    MILLILITER = "milliliter"
    LITER = "liter"
    PACK = "pack"


@dataclass(frozen=True)
class Quantity:
    """An immutable amount of something, e.g. 2 pieces or 500 grams."""

    amount: float
    unit: Unit

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValidationError("Quantity amount cannot be negative.")
        if not isinstance(self.unit, Unit):
            raise ValidationError("Quantity unit must be a valid Unit.")

    def add(self, other: "Quantity") -> "Quantity":
        """Return a new Quantity with amounts summed (units must match)."""
        if self.unit != other.unit:
            raise ValidationError(
                f"Cannot add quantities with different units: "
                f"{self.unit} and {other.unit}."
            )
        return Quantity(amount=self.amount + other.amount, unit=self.unit)

    def subtract(self, other: "Quantity") -> "Quantity":
        """Return a new Quantity with the other amount removed."""
        if self.unit != other.unit:
            raise ValidationError(
                f"Cannot subtract quantities with different units: "
                f"{self.unit} and {other.unit}."
            )
        result = self.amount - other.amount
        if result < 0:
            raise ValidationError("Resulting quantity cannot be negative.")
        return Quantity(amount=result, unit=self.unit)

    @property
    def is_empty(self) -> bool:
        return self.amount == 0
