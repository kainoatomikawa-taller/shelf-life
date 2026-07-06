"""Data transfer objects for user onboarding / taste profile use cases.

These are plain data contracts that cross the boundary between the interfaces
layer and the application layer. They never expose domain entities directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlavorProfileInput:
    sweetness: float = 0.5
    saltiness: float = 0.5
    sourness: float = 0.5
    bitterness: float = 0.5
    spiciness: float = 0.5
    umami: float = 0.5


@dataclass(frozen=True)
class SubmitOnboardingInput:
    user_id: str
    allergies: tuple[str, ...] = ()
    diet_type: str = "omnivore"
    disliked_ingredients: tuple[str, ...] = ()
    liked_cuisines: tuple[str, ...] = ()
    flavor_profile: FlavorProfileInput = field(default_factory=FlavorProfileInput)
    skill_level: str = "beginner"
    typical_time_available_minutes: int = 30
    equipment: tuple[str, ...] = ()
    budget_sensitivity: str = "medium"
    adventurousness: float = 0.5


@dataclass(frozen=True)
class UserProfileOutput:
    id: str
    allergies: tuple[str, ...]
    diet_type: str
    disliked_ingredients: tuple[str, ...]
    liked_cuisines: tuple[str, ...]
    flavor_profile: dict[str, float]
    skill_level: str
    typical_time_available_minutes: int
    equipment: tuple[str, ...]
    budget_sensitivity: str
    adventurousness: float
    taste_vector: dict[str, float]
