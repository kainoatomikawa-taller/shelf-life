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


class FlavorProfileRequest(BaseModel):
    sweetness: float = Field(0.5, ge=0.0, le=1.0)
    saltiness: float = Field(0.5, ge=0.0, le=1.0)
    sourness: float = Field(0.5, ge=0.0, le=1.0)
    bitterness: float = Field(0.5, ge=0.0, le=1.0)
    spiciness: float = Field(0.5, ge=0.0, le=1.0)
    umami: float = Field(0.5, ge=0.0, le=1.0)


class OnboardingRequest(BaseModel):
    """Body for submitting the onboarding flow (§5.1). Every field is
    optional — steps are skippable and fall back to domain defaults."""

    allergies: list[str] = Field(default_factory=list)
    diet_type: str = "omnivore"
    disliked_ingredients: list[str] = Field(default_factory=list)
    liked_cuisines: list[str] = Field(default_factory=list)
    flavor_profile: FlavorProfileRequest = Field(
        default_factory=FlavorProfileRequest
    )
    skill_level: str = "beginner"
    typical_time_available_minutes: int = Field(30, gt=0)
    equipment: list[str] = Field(default_factory=list)
    budget_sensitivity: str = "medium"
    adventurousness: float = Field(0.5, ge=0.0, le=1.0)


class UserProfileResponse(BaseModel):
    id: str
    allergies: list[str]
    diet_type: str
    disliked_ingredients: list[str]
    liked_cuisines: list[str]
    flavor_profile: dict[str, float]
    skill_level: str
    typical_time_available_minutes: int
    equipment: list[str]
    budget_sensitivity: str
    adventurousness: float
    taste_vector: dict[str, float]
