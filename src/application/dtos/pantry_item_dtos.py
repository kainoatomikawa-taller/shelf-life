"""Data transfer objects for pantry item use cases.

These are plain data contracts that cross the boundary between the interfaces
layer and the application layer. They never expose domain entities directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AddPantryItemInput:
    owner_id: str
    name: str
    amount: float
    unit: str
    expiration_date: date


@dataclass(frozen=True)
class PantryItemOutput:
    id: str
    owner_id: str
    name: str
    amount: float
    unit: str
    expiration_date: date
    freshness_status: str
    days_until_expiration: int


@dataclass(frozen=True)
class ListPantryItemsInput:
    owner_id: str


@dataclass(frozen=True)
class ConsumePantryItemInput:
    item_id: str
    amount: float
    unit: str
