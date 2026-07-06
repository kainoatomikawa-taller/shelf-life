"""SubstitutionEngine domain service.

Given an ingredient a recipe calls for but the user is missing, decides
which catalog substitutions (§5.5) are safe and useful to suggest instead.
Pure logic, no I/O: candidate Substitutions and the Ingredient catalog are
looked up by the caller (an application-layer use case) and handed in here.

A candidate survives only if it clears every gate:
* it targets the missing ingredient
* its confidence is at or above the threshold (AC2)
* it's valid for the cooking context — GENERAL or a context match (AC3)
* the user actually has the replacement on hand
* the replacement never crosses a hard constraint — allergy or diet (AC1)

Hard-constraint safety is never relaxed by confidence or context: a
high-confidence, context-valid swap that contains a user's allergen is
still rejected.
"""

from __future__ import annotations

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.exceptions import IngredientNotFoundError
from src.domain.value_objects.substitution_context import SubstitutionContext
from src.domain.value_objects.substitution_suggestion import SubstitutionSuggestion

DEFAULT_CONFIDENCE_THRESHOLD = 0.8


class SubstitutionEngine:
    """Filters candidate substitutions down to ones that are safe to serve."""

    def find_valid_substitutions(
        self,
        missing_ingredient_id: str,
        context: SubstitutionContext,
        user: User,
        available_ingredient_ids: set[str],
        candidates: list[Substitution],
        ingredients_by_id: dict[str, Ingredient],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> list[SubstitutionSuggestion]:
        """Return safe substitutions for `missing_ingredient_id`, most
        confident first.
        """
        if missing_ingredient_id not in ingredients_by_id:
            raise IngredientNotFoundError(missing_ingredient_id)

        suggestions = []
        for candidate in candidates:
            if candidate.from_ingredient_id != missing_ingredient_id:
                continue
            if not candidate.meets_confidence_threshold(confidence_threshold):
                continue
            if not candidate.is_valid_for_context(context):
                continue
            if candidate.to_ingredient_id not in available_ingredient_ids:
                continue

            substitute = self._lookup(ingredients_by_id, candidate.to_ingredient_id)
            if not user.hard_constraints.permits(
                substitute.allergen_tags, substitute.diet_tags
            ):
                continue

            suggestions.append(SubstitutionSuggestion(substitution=candidate))

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)

    @staticmethod
    def _lookup(
        ingredients_by_id: dict[str, Ingredient], ingredient_id: str
    ) -> Ingredient:
        ingredient = ingredients_by_id.get(ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(ingredient_id)
        return ingredient
