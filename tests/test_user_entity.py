"""Unit tests for the User entity, its taste vector, and hard/soft field split."""

import pytest

from src.domain.entities.user import User
from src.domain.exceptions import ValidationError
from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.taste_vector import TasteVector


def _user(**pref_overrides: object) -> User:
    preferences = SoftPreferences(**pref_overrides)  # type: ignore[arg-type]
    hard_constraints = HardConstraints(allergies=["Peanuts"], diet_type=DietType.VEGAN)
    return User(id="user-1", hard_constraints=hard_constraints, preferences=preferences)


def test_hard_constraints_are_normalized_and_separate_from_preferences() -> None:
    user = _user()
    assert user.hard_constraints.allergies == ("peanuts",)
    assert user.hard_constraints.diet_type == DietType.VEGAN
    assert isinstance(user.preferences, SoftPreferences)


def test_flavor_profile_supports_slider_dimensions() -> None:
    profile = FlavorProfile(sweetness=0.9, spiciness=0.1)
    user = _user(flavor_profile=profile)
    assert user.preferences.flavor_profile.sweetness == 0.9
    assert user.preferences.flavor_profile.spiciness == 0.1


def test_flavor_profile_rejects_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        FlavorProfile(sweetness=1.5)


def test_taste_vector_is_seeded_from_flavor_profile() -> None:
    profile = FlavorProfile(sweetness=0.8, saltiness=0.2)
    user = _user(flavor_profile=profile)
    assert user.taste_vector.as_dict()["sweetness"] == 0.8
    assert user.taste_vector.as_dict()["saltiness"] == 0.2


def test_high_rating_pulls_taste_vector_toward_recipe() -> None:
    user = _user(flavor_profile=FlavorProfile(sweetness=0.5))
    before = user.taste_vector.as_dict()["sweetness"]

    user.record_rating(FlavorProfile(sweetness=1.0), rating=5.0)

    after = user.taste_vector.as_dict()["sweetness"]
    assert after > before


def test_low_rating_pushes_taste_vector_away_from_recipe() -> None:
    user = _user(flavor_profile=FlavorProfile(sweetness=0.5))
    before = user.taste_vector.as_dict()["sweetness"]

    user.record_rating(FlavorProfile(sweetness=1.0), rating=1.0)

    after = user.taste_vector.as_dict()["sweetness"]
    assert after < before


def test_neutral_rating_does_not_move_taste_vector() -> None:
    user = _user(flavor_profile=FlavorProfile(sweetness=0.5))
    user.record_rating(FlavorProfile(sweetness=1.0), rating=3.0)
    assert user.taste_vector.as_dict()["sweetness"] == 0.5


def test_rating_out_of_range_is_rejected() -> None:
    user = _user()
    with pytest.raises(ValidationError):
        user.record_rating(FlavorProfile(), rating=6.0)


def test_known_quick_tag_lowers_matching_dimension_even_on_a_high_rating() -> None:
    user = _user(flavor_profile=FlavorProfile(spiciness=0.5))
    before = user.taste_vector.as_dict()["spiciness"]

    user.record_rating(
        FlavorProfile(spiciness=1.0), rating=5.0, quick_tags=["too spicy"]
    )

    after = user.taste_vector.as_dict()["spiciness"]
    # The 5-star rating alone would pull spiciness up toward the recipe's
    # 1.0; the "too spicy" tag should override that and pull it down instead.
    assert after < before


def test_known_quick_tag_raises_matching_dimension() -> None:
    user = _user(flavor_profile=FlavorProfile(saltiness=0.5))
    before = user.taste_vector.as_dict()["saltiness"]

    user.record_rating(
        FlavorProfile(saltiness=0.5), rating=3.0, quick_tags=["not salty enough"]
    )

    after = user.taste_vector.as_dict()["saltiness"]
    assert after > before


def test_unrecognized_quick_tags_do_not_move_the_taste_vector() -> None:
    user = _user(flavor_profile=FlavorProfile(spiciness=0.5))
    before = user.taste_vector.as_dict()

    user.record_rating(
        FlavorProfile(spiciness=0.5), rating=3.0, quick_tags=["easy", "kid-approved"]
    )

    assert user.taste_vector.as_dict() == before


def test_has_allergy_conflict_matches_case_insensitively() -> None:
    user = _user()
    assert user.has_allergy_conflict(["Peanuts", "soy"]) is True
    assert user.has_allergy_conflict(["shellfish"]) is False


def test_update_preferences_replaces_but_not_hard_constraints() -> None:
    user = _user()
    new_preferences = SoftPreferences(skill_level=SkillLevel.ADVANCED)
    user.update_preferences(new_preferences)
    assert user.preferences.skill_level == SkillLevel.ADVANCED
    assert user.hard_constraints.diet_type == DietType.VEGAN


def test_update_hard_constraints_replaces_but_not_preferences() -> None:
    user = _user()
    new_constraints = HardConstraints(allergies=["dairy"], diet_type=DietType.KETO)
    user.update_hard_constraints(new_constraints)
    assert user.hard_constraints.diet_type == DietType.KETO
    assert user.hard_constraints.allergies == ("dairy",)


def test_missing_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        User(
            id="",
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )


def test_explicit_taste_vector_is_respected() -> None:
    vector = TasteVector.from_flavor_profile(FlavorProfile(umami=0.9))
    user = User(
        id="user-2",
        hard_constraints=HardConstraints(),
        preferences=SoftPreferences(),
        taste_vector=vector,
    )
    assert user.taste_vector.as_dict()["umami"] == 0.9
