"""Unit tests for SpoilageCheckGuidanceResolver.resolve."""

from src.domain.services.spoilage_check_guidance_resolver import (
    SpoilageCheckGuidanceResolver,
)
from src.domain.value_objects.ingredient_category import IngredientCategory


def test_every_category_has_a_tip() -> None:
    resolver = SpoilageCheckGuidanceResolver()
    for category in IngredientCategory:
        tip = resolver.resolve(category)
        assert tip.smell
        assert tip.look
        assert tip.texture


def test_tips_differ_by_category() -> None:
    resolver = SpoilageCheckGuidanceResolver()
    fridge_tip = resolver.resolve(IngredientCategory.PERISHABLE_FRIDGE)
    frozen_tip = resolver.resolve(IngredientCategory.FROZEN)
    assert fridge_tip != frozen_tip


def test_spice_guidance_does_not_read_as_a_safety_alarm() -> None:
    tip = SpoilageCheckGuidanceResolver().resolve(IngredientCategory.SPICE)
    assert "safe" in tip.smell.lower()
