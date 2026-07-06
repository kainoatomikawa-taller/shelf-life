"""Pydantic request/response schemas.

Schema validation only (shape, types, required fields). Business rules are
enforced in the domain layer, not here.
"""

from __future__ import annotations

from datetime import date, datetime

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


class IngredientSummaryResponse(BaseModel):
    id: str
    name: str
    aliases: list[str]
    category: str
    default_storage_location: str


class AddInventoryItemRequest(BaseModel):
    """Body for adding an inventory item from the add-item screen (§5.2).

    Only ingredient_id is required — quantity_state and storage_location
    fall back to smart defaults when omitted, and the dates are left for
    the freshness engine to estimate around when skipped.
    """

    user_id: str = Field(..., min_length=1)
    ingredient_id: str = Field(..., min_length=1)
    quantity_state: str | None = None
    storage_location: str | None = None
    purchase_date: date | None = None
    printed_package_date: date | None = None
    is_frozen: bool = False
    notes: str | None = None


class InventoryItemResponse(BaseModel):
    id: str
    user_id: str
    ingredient_id: str
    ingredient_name: str
    quantity_state: str
    storage_location: str
    purchase_date: date | None
    printed_package_date: date | None
    is_frozen: bool
    computed_freshness_date: date
    freshness_date_type: str
    freshness_status: str
    added_at: datetime
    notes: str | None


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
