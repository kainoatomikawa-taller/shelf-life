"""Unit tests for the Substitution entity's confidence and context checks."""

import pytest

from src.domain.entities.substitution import Substitution
from src.domain.exceptions import ValidationError
from src.domain.value_objects.substitution_context import SubstitutionContext


def _substitution(**overrides: object) -> Substitution:
    defaults: dict = dict(
        id="sub-1",
        from_ingredient_id="ingredient-buttermilk",
        to_ingredient_id="ingredient-milk-vinegar",
        context=SubstitutionContext.BAKING,
        confidence=0.9,
    )
    defaults.update(overrides)
    return Substitution(**defaults)  # type: ignore[arg-type]


def test_meets_confidence_threshold() -> None:
    substitution = _substitution(confidence=0.8)
    assert substitution.meets_confidence_threshold(0.8) is True
    assert substitution.meets_confidence_threshold(0.81) is False


def test_general_context_is_valid_everywhere() -> None:
    substitution = _substitution(context=SubstitutionContext.GENERAL)
    assert substitution.is_valid_for_context(SubstitutionContext.BAKING) is True
    assert substitution.is_valid_for_context(SubstitutionContext.SAVORY) is True


def test_specific_context_only_matches_itself() -> None:
    substitution = _substitution(context=SubstitutionContext.BAKING)
    assert substitution.is_valid_for_context(SubstitutionContext.BAKING) is True
    assert substitution.is_valid_for_context(SubstitutionContext.SAVORY) is False


def test_rejects_self_referential_substitution() -> None:
    with pytest.raises(ValidationError):
        _substitution(
            from_ingredient_id="ingredient-1", to_ingredient_id="ingredient-1"
        )


def test_rejects_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        _substitution(confidence=1.5)
