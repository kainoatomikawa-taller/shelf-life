"""TasteVector value object.

A derived numeric fingerprint of a user's taste, expressed across the same
dimensions as FlavorProfile. It is seeded from the user's declared flavor
profile and drifts over time as ratings arrive: a highly-rated recipe pulls
the vector toward that recipe's flavor profile, a poorly-rated one pushes it
away. It is never edited directly — only derived and updated via ratings.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import ValidationError
from src.domain.value_objects.flavor_profile import FLAVOR_DIMENSIONS, FlavorProfile

MIN_RATING = 1.0
MAX_RATING = 5.0
NEUTRAL_RATING = 3.0
DEFAULT_LEARNING_RATE = 0.15


@dataclass(frozen=True)
class TasteVector:
    weights: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.weights) != len(FLAVOR_DIMENSIONS):
            raise ValidationError(
                f"TasteVector must have {len(FLAVOR_DIMENSIONS)} weights, "
                f"got {len(self.weights)}."
            )
        if any(not (0.0 <= w <= 1.0) for w in self.weights):
            raise ValidationError(
                "TasteVector weights must all be between 0.0 and 1.0."
            )

    @classmethod
    def from_flavor_profile(cls, flavor_profile: FlavorProfile) -> "TasteVector":
        """Seed a taste vector from a user's declared flavor profile."""
        return cls(weights=flavor_profile.as_tuple())

    def as_dict(self) -> dict[str, float]:
        return dict(zip(FLAVOR_DIMENSIONS, self.weights, strict=True))

    def updated_with_rating(
        self,
        recipe_flavor_profile: FlavorProfile,
        rating: float,
        learning_rate: float = DEFAULT_LEARNING_RATE,
    ) -> "TasteVector":
        """Return a new vector nudged by a 1-5 rating of a recipe.

        Ratings above NEUTRAL_RATING pull each dimension toward the recipe's
        value; ratings below it push away. A neutral rating is a no-op.
        """
        if not (MIN_RATING <= rating <= MAX_RATING):
            raise ValidationError(
                f"rating must be between {MIN_RATING} and {MAX_RATING}, got {rating}."
            )

        pull = (
            (rating - NEUTRAL_RATING) / (MAX_RATING - NEUTRAL_RATING)
        ) * learning_rate
        recipe_weights = recipe_flavor_profile.as_tuple()
        new_weights = tuple(
            max(0.0, min(1.0, current + pull * (target - current)))
            for current, target in zip(self.weights, recipe_weights, strict=True)
        )
        return TasteVector(weights=new_weights)
