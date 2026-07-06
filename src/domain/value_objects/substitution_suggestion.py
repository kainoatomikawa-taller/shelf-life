"""SubstitutionSuggestion value object.

The result of the substitution engine: a Substitution that has already
cleared every safety and quality gate (hard constraints, confidence,
context), paired with a disclosure string that is always present — callers
never need to null-check impact_note before showing it to a user (§5.5 AC3).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.substitution import Substitution


@dataclass(frozen=True)
class SubstitutionSuggestion:
    substitution: Substitution

    @property
    def to_ingredient_id(self) -> str:
        return self.substitution.to_ingredient_id

    @property
    def confidence(self) -> float:
        return self.substitution.confidence

    @property
    def disclosure(self) -> str:
        """Human-readable summary of the swap's impact, always non-empty."""
        if self.substitution.impact_note:
            return self.substitution.impact_note
        if self.substitution.ratio_note:
            return (
                f"No noted flavor or texture impact. "
                f"Ratio: {self.substitution.ratio_note}."
            )
        return "No noted impact on flavor, texture, or ratio."
