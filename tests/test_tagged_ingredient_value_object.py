"""Unit tests for the TaggedIngredient value object."""

import pytest

from src.domain.exceptions import ValidationError
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.tagged_ingredient import TaggedIngredient


def test_is_matched_true_when_ingredient_id_present() -> None:
    tagged = TaggedIngredient(
        raw_text="2 cups flour",
        ingredient_id="ingredient-flour",
        role=IngredientRole.ESSENTIAL,
    )
    assert tagged.is_matched is True


def test_is_matched_false_when_ingredient_id_is_none() -> None:
    tagged = TaggedIngredient(
        raw_text="1 tbsp fairy dust", ingredient_id=None, role=IngredientRole.OPTIONAL
    )
    assert tagged.is_matched is False


def test_rejects_empty_raw_text() -> None:
    with pytest.raises(ValidationError):
        TaggedIngredient(raw_text="", ingredient_id=None, role=IngredientRole.ESSENTIAL)


def test_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        TaggedIngredient(raw_text="flour", ingredient_id=None, role="essential")  # type: ignore[arg-type]
