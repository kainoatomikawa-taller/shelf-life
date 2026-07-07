"""TaggedIngredient value object.

The result of resolving one line of a raw recipe's freeform ingredient text
against the ingredient catalog: which catalog entry (if any) it maps to, and
whether the recipe requires it or could do without it. ingredient_id is None
when nothing in the catalog could be confidently matched to raw_text —
pipeline consumers (e.g. a human review queue) must treat that as "needs a
human," never silently drop the ingredient or publish it unmapped.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import ValidationError
from src.domain.value_objects.ingredient_role import IngredientRole


@dataclass(frozen=True)
class TaggedIngredient:
    raw_text: str
    ingredient_id: str | None
    role: IngredientRole

    def __post_init__(self) -> None:
        if not self.raw_text or not self.raw_text.strip():
            raise ValidationError("TaggedIngredient raw_text is required.")
        if not isinstance(self.role, IngredientRole):
            raise ValidationError(
                "TaggedIngredient role must be a valid IngredientRole."
            )

    @property
    def is_matched(self) -> bool:
        return self.ingredient_id is not None
