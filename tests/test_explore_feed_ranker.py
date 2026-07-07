"""Unit tests for ExploreFeedRanker — §10 Step 4 Explore feed ranking.

Covers all three acceptance criteria:
1. Explore ranks by popularity then novelty.
2. Adventurousness slider controls stretch amount.
3. Cautious users get adjacent recommendations.
"""

import pytest

from src.domain.entities.recipe import Recipe
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError
from src.domain.services.explore_feed_ranker import (
    DEFAULT_WEIGHTS,
    MAX_NOVELTY_TARGET,
    MIN_NOVELTY_TARGET,
    ExploreFeedRanker,
)
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.taste_vector import TasteVector

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"

# A neutral TasteVector (all 0.5) makes flavor_profile distance easy to
# reason about: FlavorProfile(<dim>=0.5 + d) sits exactly `d` away on that
# dimension and 0.0 away on every other, so novelty == d / sqrt(6).
_NEUTRAL_TASTE = TasteVector.from_flavor_profile(FlavorProfile())

# A zero-baseline TasteVector makes novelty exactly controllable: setting
# every FlavorProfile dimension to the same value `t` puts the recipe at
# Euclidean distance t * sqrt(6) from the zero vector, which normalizes
# back to exactly `t`.
_ZERO_TASTE = TasteVector(weights=(0.0,) * 6)


def _flavor_profile_at_novelty(novelty: float) -> FlavorProfile:
    return FlavorProfile(
        sweetness=novelty,
        saltiness=novelty,
        sourness=novelty,
        bitterness=novelty,
        spiciness=novelty,
        umami=novelty,
    )


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-1",
        name="Recipe",
        ingredients=[RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL)],
        steps=["Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
        popularity_score=0.5,
        flavor_profile=FlavorProfile(),
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user(
    adventurousness: float = 0.5, taste_vector: TasteVector = _NEUTRAL_TASTE
) -> User:
    return User(
        id="user-1",
        hard_constraints=HardConstraints(),
        preferences=SoftPreferences(adventurousness=adventurousness),
        taste_vector=taste_vector,
    )


def _ranker(**kwargs: object) -> ExploreFeedRanker:
    return ExploreFeedRanker(**kwargs)  # type: ignore[arg-type]


# --- AC1: popularity-primary weighted blend + weight validation ------------


def test_total_score_matches_manual_weighted_sum() -> None:
    ranker = _ranker()
    user = _user()
    result = ranker.score(
        _recipe(popularity_score=0.6, flavor_profile=FlavorProfile(sweetness=0.8)),
        user,
    )

    expected = (
        DEFAULT_WEIGHTS["popularity"] * result.popularity_score
        + DEFAULT_WEIGHTS["novelty_fit"] * result.novelty_fit_score
    )
    assert result.total_score == pytest.approx(expected)


def test_popularity_weighted_higher_than_novelty_fit() -> None:
    assert DEFAULT_WEIGHTS["popularity"] > DEFAULT_WEIGHTS["novelty_fit"]


def test_higher_popularity_outranks_lower_popularity_at_same_novelty_fit() -> None:
    ranker = _ranker()
    user = _user(adventurousness=0.5)
    low_pop = _recipe(id="low-pop", popularity_score=0.2)
    high_pop = _recipe(id="high-pop", popularity_score=0.9)

    ranked = ranker.rank([low_pop, high_pop], user)

    assert [s.recipe_id for s in ranked] == ["high-pop", "low-pop"]


def test_rank_orders_most_recommended_first() -> None:
    ranker = _ranker()
    user = _user()
    a = _recipe(id="a", popularity_score=0.1)
    b = _recipe(id="b", popularity_score=0.9)
    c = _recipe(id="c", popularity_score=0.5)

    ranked = ranker.rank([a, b, c], user)

    scores = [s.total_score for s in ranked]
    assert scores == sorted(scores, reverse=True)


def test_weights_must_have_exactly_the_default_keys() -> None:
    with pytest.raises(ValidationError):
        _ranker(weights={"popularity": 1.0})


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValidationError):
        _ranker(weights={"popularity": 0.5, "novelty_fit": 0.4})


# --- AC2: adventurousness slider controls stretch amount --------------------


def test_higher_adventurousness_favors_more_novel_recipes() -> None:
    ranker = _ranker()
    mild = _recipe(id="mild", popularity_score=0.5, flavor_profile=FlavorProfile())
    bold = _recipe(
        id="bold",
        popularity_score=0.5,
        flavor_profile=FlavorProfile(sweetness=0.0, saltiness=0.0, sourness=0.0),
    )

    cautious_ranking = [s.recipe_id for s in ranker.rank([mild, bold], _user(0.0))]
    adventurous_ranking = [s.recipe_id for s in ranker.rank([mild, bold], _user(1.0))]

    assert cautious_ranking == ["mild", "bold"]
    assert adventurous_ranking == ["bold", "mild"]


def test_novelty_fit_target_scales_linearly_with_adventurousness() -> None:
    ranker = _ranker()
    # A recipe whose novelty sits exactly at the cautious-end target should
    # score a perfect novelty_fit for a fully cautious user, and a recipe at
    # the adventurous-end target should score a perfect novelty_fit for a
    # fully adventurous user.
    cautious_target_recipe = _recipe(
        flavor_profile=_flavor_profile_at_novelty(MIN_NOVELTY_TARGET)
    )
    adventurous_target_recipe = _recipe(
        flavor_profile=_flavor_profile_at_novelty(MAX_NOVELTY_TARGET)
    )

    cautious_result = ranker.score(
        cautious_target_recipe, _user(0.0, taste_vector=_ZERO_TASTE)
    )
    adventurous_result = ranker.score(
        adventurous_target_recipe, _user(1.0, taste_vector=_ZERO_TASTE)
    )

    assert cautious_result.novelty_fit_score == pytest.approx(1.0, abs=1e-6)
    assert adventurous_result.novelty_fit_score == pytest.approx(1.0, abs=1e-6)


# --- AC3: cautious users get adjacent recommendations ------------------------


def test_cautious_user_prefers_adjacent_novelty_over_identical_or_far() -> None:
    ranker = _ranker()
    user = _user(adventurousness=0.0)

    identical = _recipe(
        id="identical", popularity_score=0.5, flavor_profile=FlavorProfile()
    )
    adjacent = _recipe(
        id="adjacent",
        popularity_score=0.5,
        flavor_profile=FlavorProfile(sweetness=0.65),
    )
    far = _recipe(
        id="far",
        popularity_score=0.5,
        flavor_profile=FlavorProfile(sweetness=1.0, saltiness=1.0, sourness=1.0),
    )

    ranked = ranker.rank([identical, adjacent, far], user)

    assert [s.recipe_id for s in ranked] == ["adjacent", "identical", "far"]


def test_cautious_user_never_targets_zero_novelty() -> None:
    assert MIN_NOVELTY_TARGET > 0.0


def test_adventurous_user_never_targets_maximal_novelty() -> None:
    assert MAX_NOVELTY_TARGET < 1.0


# --- Novelty scoring ----------------------------------------------------------


def test_novelty_is_zero_for_identical_flavor_profile() -> None:
    ranker = _ranker()
    user = _user()
    result = ranker.score(_recipe(flavor_profile=FlavorProfile()), user)

    assert result.novelty_score == pytest.approx(0.0)


def test_novelty_is_one_for_maximally_different_flavor_profile() -> None:
    ranker = _ranker()
    user = _user(taste_vector=_ZERO_TASTE)
    result = ranker.score(
        _recipe(flavor_profile=_flavor_profile_at_novelty(1.0)),
        user,
    )

    assert result.novelty_score == pytest.approx(1.0)


def test_popularity_score_is_clamped_to_zero_one() -> None:
    ranker = _ranker()
    user = _user()
    result = ranker.score(_recipe(popularity_score=5.0), user)

    assert result.popularity_score == 1.0
