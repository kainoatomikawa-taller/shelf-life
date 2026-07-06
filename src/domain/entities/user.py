"""User entity.

Represents a person using the app. Fields are split into two kinds per §4.6:

* Hard constraints (allergies, diet type) — non-negotiable. A recipe that
  violates one must never be served.
* Soft preferences (disliked ingredients, liked cuisines, flavor profile,
  skill level, time available, equipment, budget sensitivity,
  adventurousness) — used to rank and personalize, never to exclude.

The taste vector is derived from the soft flavor profile and updates as the
user rates recipes; it is never set directly by callers.
"""

from __future__ import annotations

from src.domain.exceptions import ValidationError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.taste_vector import TasteVector


class User:
    """A user's dietary constraints, taste preferences, and derived taste profile."""

    def __init__(
        self,
        id: str,
        hard_constraints: HardConstraints,
        preferences: SoftPreferences,
        taste_vector: TasteVector | None = None,
    ) -> None:
        if not id:
            raise ValidationError("User id is required.")

        self._id = id
        self._hard_constraints = hard_constraints
        self._preferences = preferences
        self._taste_vector = taste_vector or TasteVector.from_flavor_profile(
            preferences.flavor_profile
        )

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def hard_constraints(self) -> HardConstraints:
        return self._hard_constraints

    @property
    def preferences(self) -> SoftPreferences:
        return self._preferences

    @property
    def taste_vector(self) -> TasteVector:
        return self._taste_vector

    # --- Behaviour (business rules live here) -------------------------------

    def update_hard_constraints(self, hard_constraints: HardConstraints) -> None:
        """Replace the user's allergies and diet type.

        These are safety-critical, so callers must supply a complete,
        already-validated HardConstraints rather than patching individual
        fields in place.
        """
        self._hard_constraints = hard_constraints

    def update_preferences(self, preferences: SoftPreferences) -> None:
        """Replace the user's soft preferences."""
        self._preferences = preferences

    def has_allergy_conflict(self, allergen_tags: list[str]) -> bool:
        """True if any of the given allergen tags matches a user allergy."""
        return self._hard_constraints.conflicts_with(allergen_tags)

    def record_rating(
        self,
        recipe_flavor_profile: FlavorProfile,
        rating: float,
        quick_tags: list[str] | None = None,
    ) -> None:
        """Nudge the derived taste vector toward or away from a rated recipe.

        Ratings above 3 pull the vector toward the recipe's flavor profile;
        ratings below 3 push it away; 3 is neutral. Quick tags with a known
        flavor-dimension meaning (e.g. "too spicy") additionally correct
        that one dimension, regardless of the star rating.
        """
        updated = self._taste_vector.updated_with_rating(recipe_flavor_profile, rating)
        if quick_tags:
            updated = updated.updated_with_quick_tags(quick_tags)
        self._taste_vector = updated

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
