"""RecipeIngredient value object.

Binds a catalog ingredient to a role within a specific recipe. Carries no
quantity — that belongs to a future scaling/shopping-list concern, not to
matching or tagging, which is all this model needs to support today.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import ValidationError
from src.domain.value_objects.ingredient_role import IngredientRole


@dataclass(frozen=True)
class RecipeIngredient:
    ingredient_id: str
    role: IngredientRole

    def __post_init__(self) -> None:
        if not self.ingredient_id:
            raise ValidationError("RecipeIngredient ingredient_id is required.")
        if not isinstance(self.role, IngredientRole):
            raise ValidationError(
                "RecipeIngredient role must be a valid IngredientRole."
            )

    @property
    def is_essential(self) -> bool:
        return self.role is IngredientRole.ESSENTIAL
