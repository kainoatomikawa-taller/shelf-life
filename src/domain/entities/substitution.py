"""Substitution entity.

Represents a single directed substitution suggestion: "in context C, you can
use ingredient B instead of ingredient A at the given ratio, with the stated
quality impact and confidence score."

Directionality is intentional — swapping A↔B may produce different ratios
and impacts and should be modelled as a separate row.
"""

from __future__ import annotations

from src.domain.exceptions import ValidationError
from src.domain.value_objects.substitution_context import SubstitutionContext


class Substitution:
    """A catalog entry asserting that one ingredient can substitute for another."""

    def __init__(
        self,
        id: str,
        from_ingredient_id: str,
        to_ingredient_id: str,
        context: SubstitutionContext,
        confidence: float,
        ratio_note: str | None = None,
        impact_note: str | None = None,
    ) -> None:
        if not id:
            raise ValidationError("Substitution id is required.")
        if not from_ingredient_id:
            raise ValidationError("from_ingredient_id is required.")
        if not to_ingredient_id:
            raise ValidationError("to_ingredient_id is required.")
        if from_ingredient_id == to_ingredient_id:
            raise ValidationError(
                "A substitution cannot reference the same ingredient for both sides."
            )
        if not (0.0 <= confidence <= 1.0):
            raise ValidationError(
                f"confidence must be between 0.0 and 1.0 inclusive, got {confidence}."
            )

        self._id = id
        self._from_ingredient_id = from_ingredient_id
        self._to_ingredient_id = to_ingredient_id
        self._context = context
        self._confidence = confidence
        self._ratio_note = ratio_note.strip() if ratio_note and ratio_note.strip() else None
        self._impact_note = impact_note.strip() if impact_note and impact_note.strip() else None

    # --- Identity & read-only accessors ----------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def from_ingredient_id(self) -> str:
        return self._from_ingredient_id

    @property
    def to_ingredient_id(self) -> str:
        return self._to_ingredient_id

    @property
    def context(self) -> SubstitutionContext:
        return self._context

    @property
    def confidence(self) -> float:
        return self._confidence

    @property
    def ratio_note(self) -> str | None:
        return self._ratio_note

    @property
    def impact_note(self) -> str | None:
        return self._impact_note

    # --- Behaviour -------------------------------------------------------------

    def meets_confidence_threshold(self, threshold: float) -> bool:
        """True when this substitution's confidence is at or above the threshold.

        Callers use this to filter suggestions: e.g. only surface substitutions
        where meets_confidence_threshold(0.8) is True.
        """
        return self._confidence >= threshold

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Substitution):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
