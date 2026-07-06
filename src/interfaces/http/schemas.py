"""Pydantic request/response schemas.

Schema validation only (shape, types, required fields). Business rules are
enforced in the domain layer, not here.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AddPantryItemRequest(BaseModel):
    owner_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., ge=0)
    unit: str = Field(..., min_length=1)
    expiration_date: date


class ConsumePantryItemRequest(BaseModel):
    amount: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)


class PantryItemResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    amount: float
    unit: str
    expiration_date: date
    freshness_status: str
    days_until_expiration: int
