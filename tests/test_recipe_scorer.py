"""Unit tests for RecipeScorer — §10 Step 3 content-based ranking.

Covers all three acceptance criteria:
1. Score blends taste, effort, freshness, substitution penalty (and budget fit).
2. Discover ranking rewards fewer/cheaper missing items.
3. Freshness boost measurably lifts recipes using expiring items.
"""

import pytest

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.exceptions import ValidationError
from src.domain.services.recipe_scorer import DEFAULT_WEIGHTS, RecipeScorer
from src.domain.value_objects.budget_sensitivity import BudgetSensitivity
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from src.domain.value_objects.substitution_context import SubstitutionContext
from src.domain.value_objects.taste_vector import TasteVector

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
ALMOND_MILK = "ingredient-almond-milk"
BUTTER = "ingredient-butter"


def _ingredient(id: str) -> Ingredient:
    return Ingredient(
        id=id,
        name=id,
        aliases=[],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=[],
        diet_tags=[],
    )


def _catalog() -> dict[str, Ingredient]:
    return {i: _ingredient(i) for i in (FLOUR, EGGS, MILK, ALMOND_MILK, BUTTER)}


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-pancakes",
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(BUTTER, IngredientRole.OPTIONAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
        equipment_needed=["griddle"],
        flavor_profile=FlavorProfile(sweetness=0.7),
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user(
    taste_vector: TasteVector | None = None,
    skill_level: SkillLevel = SkillLevel.BEGINNER,
    typical_time_available_minutes: int = 30,
    equipment: tuple[str, ...] = ("griddle",),
    budget_sensitivity: BudgetSensitivity = BudgetSensitivity.MEDIUM,
) -> User:
    preferences = SoftPreferences(
        skill_level=skill_level,
        typical_time_available_minutes=typical_time_available_minutes,
        equipment=equipment,
        budget_sensitivity=budget_sensitivity,
    )
    return User(
        id="user-1",
        hard_constraints=HardConstraints(),
        preferences=preferences,
        taste_vector=taste_vector,
    )


def _substitution(**overrides: object) -> Substitution:
    defaults: dict = dict(
        id="sub-1",
        from_ingredient_id=MILK,
        to_ingredient_id=ALMOND_MILK,
        context=SubstitutionContext.GENERAL,
        confidence=0.9,
    )
    defaults.update(overrides)
    return Substitution(**defaults)  # type: ignore[arg-type]


def _scorer(**kwargs: object) -> RecipeScorer:
    return RecipeScorer(**kwargs)  # type: ignore[arg-type]


def _score(
    scorer: RecipeScorer,
    recipe: Recipe,
    user: User,
    available: set[str],
    freshness: dict[str, FreshnessDisplayStatus] | None = None,
    candidates: dict[str, list[Substitution]] | None = None,
    cost_by_id: dict[str, float] | None = None,
):
    return scorer.score(
        recipe,
        user=user,
        available_ingredient_ids=available,
        freshness_by_ingredient_id=freshness or {},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id=candidates or {},
        ingredients_by_id=_catalog(),
        ingredient_cost_by_id=cost_by_id,
    )


# --- AC1: weighted blend + weight validation --------------------------------


def test_total_score_matches_manual_weighted_sum() -> None:
    scorer = _scorer()
    user = _user(
        taste_vector=TasteVector.from_flavor_profile(FlavorProfile(sweetness=0.7))
    )
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})

    expected = (
        DEFAULT_WEIGHTS["taste"] * result.taste_score
        + DEFAULT_WEIGHTS["effort"] * result.effort_score
        + DEFAULT_WEIGHTS["freshness"] * result.freshness_score
        + DEFAULT_WEIGHTS["substitution_penalty"] * result.substitution_penalty_score
        + DEFAULT_WEIGHTS["budget_fit"] * result.budget_fit_score
    )
    assert result.total_score == pytest.approx(expected)


def test_custom_weights_are_honored() -> None:
    weights = {
        "taste": 1.0,
        "effort": 0.0,
        "freshness": 0.0,
        "substitution_penalty": 0.0,
        "budget_fit": 0.0,
    }
    scorer = _scorer(weights=weights)
    user = _user(
        taste_vector=TasteVector.from_flavor_profile(FlavorProfile(sweetness=0.7))
    )
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.total_score == pytest.approx(result.taste_score)


def test_weights_missing_a_key_are_rejected() -> None:
    with pytest.raises(ValidationError):
        _scorer(weights={"taste": 1.0})


def test_weights_not_summing_to_one_are_rejected() -> None:
    bad_weights = dict(DEFAULT_WEIGHTS)
    bad_weights["taste"] += 0.5
    with pytest.raises(ValidationError):
        _scorer(weights=bad_weights)


# --- Taste -------------------------------------------------------------------


def test_taste_score_is_perfect_for_identical_flavor_profile() -> None:
    scorer = _scorer()
    profile = FlavorProfile(sweetness=0.7)
    user = _user(taste_vector=TasteVector.from_flavor_profile(profile))
    result = _score(
        scorer,
        _recipe(flavor_profile=profile),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
    )
    assert result.taste_score == pytest.approx(1.0)


def test_taste_score_is_zero_for_maximally_opposite_flavor_profile() -> None:
    scorer = _scorer()
    user = _user(taste_vector=TasteVector(weights=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
    recipe = _recipe(flavor_profile=FlavorProfile(1.0, 1.0, 1.0, 1.0, 1.0, 1.0))
    result = _score(scorer, recipe, user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.taste_score == pytest.approx(0.0)


# --- Effort ------------------------------------------------------------------


def test_effort_score_is_perfect_when_time_skill_and_equipment_all_fit() -> None:
    scorer = _scorer()
    user = _user(
        skill_level=SkillLevel.BEGINNER,
        typical_time_available_minutes=30,
        equipment=("griddle",),
    )
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.effort_score == pytest.approx(1.0)


def test_effort_score_drops_when_recipe_takes_longer_than_available_time() -> None:
    scorer = _scorer()
    user = _user(typical_time_available_minutes=10)  # recipe takes 20
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.effort_score < 1.0


def test_effort_score_drops_when_recipe_is_harder_than_users_skill() -> None:
    scorer = _scorer()
    user = _user(skill_level=SkillLevel.BEGINNER)
    result = _score(
        scorer,
        _recipe(difficulty=SkillLevel.ADVANCED),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
    )
    assert result.effort_score < 1.0


def test_effort_score_drops_when_user_lacks_needed_equipment() -> None:
    scorer = _scorer()
    user = _user(equipment=())
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.effort_score < 1.0


# --- AC3: freshness boost ----------------------------------------------------


def test_freshness_score_is_zero_with_no_expiring_ingredients() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(
        scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER}, freshness={}
    )
    assert result.freshness_score == 0.0


def test_freshness_score_is_positive_when_recipe_uses_an_expiring_ingredient() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={MILK: FreshnessDisplayStatus.USE_SOON},
    )
    assert result.freshness_score > 0.0


def test_freshness_score_increases_with_more_expiring_ingredients_used() -> None:
    scorer = _scorer()
    user = _user()
    one_expiring = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={MILK: FreshnessDisplayStatus.USE_SOON},
    )
    two_expiring = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={
            MILK: FreshnessDisplayStatus.USE_SOON,
            EGGS: FreshnessDisplayStatus.USE_SOON,
        },
    )
    assert two_expiring.freshness_score > one_expiring.freshness_score


def test_use_now_urgency_scores_higher_than_use_soon() -> None:
    scorer = _scorer()
    user = _user()
    use_now = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={MILK: FreshnessDisplayStatus.USE_NOW},
    )
    use_soon = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={MILK: FreshnessDisplayStatus.USE_SOON},
    )
    assert use_now.freshness_score > use_soon.freshness_score


def test_freshness_boost_measurably_lifts_total_score() -> None:
    """AC3 end to end: holding everything else equal, using an expiring
    ingredient must raise the recipe's total score, not just one sub-score.
    """
    scorer = _scorer()
    user = _user()
    without_boost = _score(
        scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER}
    )
    with_boost = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={MILK: FreshnessDisplayStatus.USE_NOW},
    )
    assert with_boost.total_score > without_boost.total_score


def test_optional_ingredient_expiring_still_contributes_to_freshness() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(
        scorer,
        _recipe(),  # BUTTER is optional
        user,
        available={FLOUR, EGGS, MILK, BUTTER},
        freshness={BUTTER: FreshnessDisplayStatus.USE_NOW},
    )
    assert result.freshness_score > 0.0


# --- Substitution penalty ----------------------------------------------------


def test_substitution_penalty_is_perfect_when_all_essentials_on_hand() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.substitution_penalty_score == pytest.approx(1.0)


def test_substitution_penalty_drops_when_an_essential_is_substituted() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, ALMOND_MILK},  # milk swapped for almond milk
        candidates={MILK: [_substitution()]},
    )
    assert result.substitution_penalty_score < 1.0


# --- AC2: budget fit rewards fewer/cheaper missing items ---------------------


def test_budget_fit_is_perfect_when_nothing_is_missing() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS, MILK, BUTTER})
    assert result.budget_fit_score == pytest.approx(1.0)


def test_budget_fit_drops_when_an_essential_is_missing_with_no_substitute() -> None:
    scorer = _scorer()
    user = _user()
    result = _score(scorer, _recipe(), user, available={FLOUR, EGGS})  # milk missing
    assert result.budget_fit_score < 1.0


def test_budget_fit_rewards_fewer_missing_essentials() -> None:
    scorer = _scorer()
    user = _user()
    one_missing = _score(
        scorer, _recipe(), user, available={FLOUR, EGGS}
    )  # milk missing
    two_missing = _score(
        scorer, _recipe(), user, available={FLOUR}
    )  # eggs + milk missing
    assert one_missing.budget_fit_score > two_missing.budget_fit_score


def test_budget_fit_rewards_cheaper_missing_essentials() -> None:
    scorer = _scorer()
    user = _user()
    cheap_missing = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS},
        cost_by_id={MILK: 0.5, FLOUR: 3.0, EGGS: 3.0},
    )
    expensive_missing = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS},
        cost_by_id={MILK: 5.0, FLOUR: 3.0, EGGS: 3.0},
    )
    assert cheap_missing.budget_fit_score > expensive_missing.budget_fit_score


def test_higher_budget_sensitivity_amplifies_the_missing_item_penalty() -> None:
    scorer = _scorer()
    low_sensitivity_user = _user(budget_sensitivity=BudgetSensitivity.LOW)
    high_sensitivity_user = _user(budget_sensitivity=BudgetSensitivity.HIGH)
    low = _score(scorer, _recipe(), low_sensitivity_user, available={FLOUR, EGGS})
    high = _score(scorer, _recipe(), high_sensitivity_user, available={FLOUR, EGGS})
    assert low.budget_fit_score > high.budget_fit_score


def test_missing_essential_with_a_valid_substitute_does_not_count_against_budget() -> (
    None
):
    """A substitutable ingredient isn't "missing" for budget purposes —
    only substitution_penalty should reflect it (AC1 keeps the two
    components independent).
    """
    scorer = _scorer()
    user = _user()
    result = _score(
        scorer,
        _recipe(),
        user,
        available={FLOUR, EGGS, ALMOND_MILK},
        candidates={MILK: [_substitution()]},
    )
    assert result.budget_fit_score == pytest.approx(1.0)


# --- score_all ----------------------------------------------------------------


def test_score_all_orders_recipes_by_descending_total_score() -> None:
    scorer = _scorer()
    user = _user()
    well_stocked = _recipe(id="recipe-well-stocked")
    missing_essential = _recipe(
        id="recipe-missing-essential",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(BUTTER, IngredientRole.ESSENTIAL),
        ],
    )
    results = scorer.score_all(
        [missing_essential, well_stocked],
        user=user,
        available_ingredient_ids={FLOUR, EGGS, MILK},
        freshness_by_ingredient_id={},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert [r.recipe_id for r in results] == [
        "recipe-well-stocked",
        "recipe-missing-essential",
    ]
