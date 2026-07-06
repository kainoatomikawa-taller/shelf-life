"""Mapper between the PantryItem entity and its output DTO."""

from __future__ import annotations

from datetime import date

from src.application.dtos.pantry_item_dtos import PantryItemOutput
from src.domain.entities.pantry_item import PantryItem


class PantryItemMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(item: PantryItem, today: date) -> PantryItemOutput:
        return PantryItemOutput(
            id=item.id,
            owner_id=item.owner_id,
            name=item.name,
            amount=item.quantity.amount,
            unit=item.quantity.unit.value,
            expiration_date=item.expiration_date,
            freshness_status=item.freshness_status(today),
            days_until_expiration=item.days_until_expiration(today),
        )
