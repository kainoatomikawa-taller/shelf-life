"""Unit tests for RecipeAvailabilityClassifier — §10 Steps 1-2.

Covers all three acceptance criteria:
1. Allergy/diet violations are hard-excluded.
2. Cook Now requires all essentials available or substitutable.
3. Optional missing ingredients never block a recipe.
"""

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.services.recipe_availability_classifier import (
    RecipeAvailabilityClassifier,
)
from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_availability import RecipeAvailability
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from src.domain.value_objects.substitution_context import SubstitutionContext

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
ALMOND_MILK = "ingredient-almond-milk"
VANILLA = "ingredient-vanilla"
BUTTER = "ingredient-butter"


def _ingredient(
    id: str,
    allergen_tags: list[str] | None = None,
    diet_tags: list[str] | None = None,
) -> Ingredient:
    return Ingredient(
        id=id,
        name=id,
        aliases=[],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=allergen_tags or [],
        diet_tags=diet_tags or [],
    )


def _catalog() -> dict[str, Ingredient]:
    return {
        FLOUR: _ingredient(FLOUR, diet_tags=["vegan"]),
        EGGS: _ingredient(EGGS, allergen_tags=["eggs"]),
        MILK: _ingredient(MILK, allergen_tags=["dairy"]),
        ALMOND_MILK: _ingredient(
            ALMOND_MILK, allergen_tags=["tree_nuts"], diet_tags=["vegan"]
        ),
        VANILLA: _ingredient(VANILLA, diet_tags=["vegan"]),
        BUTTER: _ingredient(BUTTER, allergen_tags=["dairy"]),
    }


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-pancakes",
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(VANILLA, IngredientRole.OPTIONAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user(
    allergies: list[str] | None = None, diet_type: DietType = DietType.OMNIVORE
) -> User:
    return User(
        id="user-1",
        hard_constraints=HardConstraints(
            allergies=allergies or [], diet_type=diet_type
        ),
        preferences=SoftPreferences(),
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


def _classifier() -> RecipeAvailabilityClassifier:
    return RecipeAvailabilityClassifier()


# --- AC1: hard filter --------------------------------------------------------


def test_hard_filter_excludes_recipe_with_allergen_conflict() -> None:
    classifier = _classifier()
    user = _user(allergies=["eggs"])
    result = classifier.filter_hard_constraints([_recipe()], user, _catalog())
    assert result == []


def test_hard_filter_excludes_recipe_incompatible_with_diet() -> None:
    classifier = _classifier()
    # Eggs and milk have no "vegan" diet tag, so a vegan recipe check fails.
    user = _user(diet_type=DietType.VEGAN)
    result = classifier.filter_hard_constraints([_recipe()], user, _catalog())
    assert result == []


def test_hard_filter_keeps_recipe_with_no_constraint_violation() -> None:
    classifier = _classifier()
    user = _user()
    result = classifier.filter_hard_constraints([_recipe()], user, _catalog())
    assert result == [_recipe()]


def test_hard_filter_is_never_overridden_by_full_stock() -> None:
    """Even if every ingredient is on hand, an allergy conflict still excludes."""
    classifier = _classifier()
    user = _user(allergies=["dairy"])
    result = classifier.classify_recipes(
        [_recipe()],
        user=user,
        available_ingredient_ids={FLOUR, EGGS, MILK, VANILLA},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert result.cook_now == ()
    assert result.discover == ()


# --- AC2: Cook Now requires essentials available or substitutable -----------


def test_cook_now_when_all_essentials_in_stock() -> None:
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={FLOUR, EGGS, MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.COOK_NOW


def test_cook_now_when_missing_essential_has_valid_substitution() -> None:
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={
            FLOUR,
            EGGS,
            ALMOND_MILK,
        },  # milk missing, has almond milk
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={MILK: [_substitution()]},
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.COOK_NOW


def test_discover_when_missing_essential_has_no_substitution() -> None:
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={FLOUR, EGGS},  # milk missing, no substitute on hand
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.DISCOVER


def test_discover_when_substitution_is_below_confidence_threshold() -> None:
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={FLOUR, EGGS, ALMOND_MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={MILK: [_substitution(confidence=0.5)]},
        ingredients_by_id=_catalog(),
        confidence_threshold=0.8,
    )
    assert bucket is RecipeAvailability.DISCOVER


def test_discover_when_substitution_valid_only_for_a_different_context() -> None:
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={FLOUR, EGGS, ALMOND_MILK},
        context=SubstitutionContext.BAKING,
        candidates_by_ingredient_id={
            MILK: [_substitution(context=SubstitutionContext.SAVORY)]
        },
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.DISCOVER


def test_discover_when_substitute_ingredient_itself_conflicts_with_allergy() -> None:
    classifier = _classifier()
    user = _user(allergies=["tree_nuts"])
    bucket = classifier.classify(
        _recipe(),
        user=user,
        available_ingredient_ids={FLOUR, EGGS, ALMOND_MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={MILK: [_substitution()]},
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.DISCOVER


# --- AC3: optional ingredients never block ----------------------------------


def test_cook_now_even_when_optional_ingredient_is_missing_and_unsubstitutable() -> (
    None
):
    classifier = _classifier()
    user = _user()
    bucket = classifier.classify(
        _recipe(),
        user=user,
        # vanilla (optional) is absent and has no candidates — must not matter.
        available_ingredient_ids={FLOUR, EGGS, MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert bucket is RecipeAvailability.COOK_NOW


# --- End-to-end grouping ------------------------------------------------------


def test_classify_recipes_splits_survivors_into_cook_now_and_discover() -> None:
    classifier = _classifier()
    user = _user()  # no allergies/diet restriction — nothing is hard-excluded
    fully_stocked = _recipe(id="recipe-fully-stocked")
    missing_essential = _recipe(
        id="recipe-missing-essential",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(BUTTER, IngredientRole.ESSENTIAL),
        ],
    )
    result = classifier.classify_recipes(
        [fully_stocked, missing_essential],
        user=user,
        available_ingredient_ids={FLOUR, EGGS, MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert result.cook_now == (fully_stocked,)
    assert result.discover == (missing_essential,)


def test_classify_recipes_drops_hard_constraint_violations_from_both_buckets() -> None:
    classifier = _classifier()
    user = _user(allergies=["dairy"])
    result = classifier.classify_recipes(
        [_recipe()],
        user=user,
        available_ingredient_ids={FLOUR, EGGS, MILK, VANILLA},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert result.cook_now == ()
    assert result.discover == ()
