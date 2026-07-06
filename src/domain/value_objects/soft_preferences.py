"""SoftPreferences value object.

Preferences that shape ranking and personalization but are never treated as
hard eligibility filters — a recipe that ignores them is still safe to
serve, just less likely to be enjoyed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.exceptions import ValidationError
from src.domain.value_objects.budget_sensitivity import BudgetSensitivity
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.skill_level import SkillLevel


@dataclass(frozen=True)
class SoftPreferences:
    disliked_ingredients: tuple[str, ...] = field(default_factory=tuple)
    liked_cuisines: tuple[str, ...] = field(default_factory=tuple)
    flavor_profile: FlavorProfile = field(default_factory=FlavorProfile)
    skill_level: SkillLevel = SkillLevel.BEGINNER
    typical_time_available_minutes: int = 30
    equipment: tuple[str, ...] = field(default_factory=tuple)
    budget_sensitivity: BudgetSensitivity = BudgetSensitivity.MEDIUM
    adventurousness: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "disliked_ingredients",
            tuple(
                i.strip().lower() for i in self.disliked_ingredients if i and i.strip()
            ),
        )
        object.__setattr__(
            self,
            "liked_cuisines",
            tuple(c.strip().lower() for c in self.liked_cuisines if c and c.strip()),
        )
        object.__setattr__(
            self,
            "equipment",
            tuple(e.strip().lower() for e in self.equipment if e and e.strip()),
        )
        if self.typical_time_available_minutes <= 0:
            raise ValidationError(
                "typical_time_available_minutes must be positive, got "
                f"{self.typical_time_available_minutes}."
            )
        if not (0.0 <= self.adventurousness <= 1.0):
            raise ValidationError(
                "adventurousness must be between 0.0 and 1.0, got "
                f"{self.adventurousness}."
            )
