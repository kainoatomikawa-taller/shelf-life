"""HardConstraints value object.

Non-negotiable dietary rules a user's recipes must never violate: allergies
that pose a safety risk, and the diet type that determines which ingredients
are permissible at all. Unlike soft preferences, a recipe that violates a
hard constraint is never served, regardless of how well it otherwise matches
the user's taste.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects.diet_type import DietType


@dataclass(frozen=True)
class HardConstraints:
    allergies: tuple[str, ...] = field(default_factory=tuple)
    diet_type: DietType = DietType.OMNIVORE

    def __post_init__(self) -> None:
        normalized = tuple(
            sorted({a.strip().lower() for a in self.allergies if a and a.strip()})
        )
        object.__setattr__(self, "allergies", normalized)

    def conflicts_with(self, allergen_tags: list[str]) -> bool:
        """True if any of the given allergen tags matches a user allergy."""
        return any(tag.strip().lower() in self.allergies for tag in allergen_tags)
