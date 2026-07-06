"""Unit tests for HardConstraints' allergy and diet compatibility checks."""

from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.hard_constraints import HardConstraints


def test_conflicts_with_matches_case_insensitively() -> None:
    constraints = HardConstraints(allergies=["Peanuts"])
    assert constraints.conflicts_with(["peanuts"]) is True
    assert constraints.conflicts_with(["Peanuts"]) is True
    assert constraints.conflicts_with(["shellfish"]) is False


def test_omnivore_is_compatible_with_any_diet_tags() -> None:
    constraints = HardConstraints(diet_type=DietType.OMNIVORE)
    assert constraints.is_compatible_with_diet([]) is True
    assert constraints.is_compatible_with_diet(["contains_dairy"]) is True


def test_vegan_requires_vegan_diet_tag() -> None:
    constraints = HardConstraints(diet_type=DietType.VEGAN)
    assert constraints.is_compatible_with_diet(["vegan", "gluten_free"]) is True
    assert constraints.is_compatible_with_diet(["vegetarian"]) is False
    assert constraints.is_compatible_with_diet([]) is False


def test_diet_tag_match_is_case_insensitive() -> None:
    constraints = HardConstraints(diet_type=DietType.VEGAN)
    assert constraints.is_compatible_with_diet(["VEGAN"]) is True


def test_permits_requires_both_no_allergy_conflict_and_diet_compatibility() -> None:
    constraints = HardConstraints(allergies=["dairy"], diet_type=DietType.VEGAN)
    assert constraints.permits([], ["vegan"]) is True
    assert constraints.permits(["dairy"], ["vegan"]) is False
    assert constraints.permits([], ["vegetarian"]) is False
