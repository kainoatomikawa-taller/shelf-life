"""Unit tests for ShoppingListGenerator — §5.4 Discover shopping list.

Covers all three acceptance criteria:
1. Only essential ingredients that are neither on hand nor substitutable
   ("true gaps") appear.
2. "have X of Y" progress spans the recipe's full ingredient list.
3. Generating the list is pure computation over true gaps only.
"""

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.services.shopping_list_generator import ShoppingListGenerator
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

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"
ALMOND_MILK = "ingredient-almond-milk"
STRAWBERRIES = "ingredient-strawberries"


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
    return {i: _ingredient(i) for i in (FLOUR, EGGS, MILK, ALMOND_MILK, STRAWBERRIES)}


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-pancakes",
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.ESSENTIAL),
            RecipeIngredient(STRAWBERRIES, IngredientRole.OPTIONAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def _user() -> User:
    return User(
        id="user-1", hard_constraints=HardConstraints(), preferences=SoftPreferences()
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


def _generator() -> ShoppingListGenerator:
    return ShoppingListGenerator()


# --- AC3: true gaps only ------------------------------------------------------


def test_true_gaps_includes_missing_essential_with_no_substitution() -> None:
    gaps = _generator().true_gaps(
        _recipe(),
        user=_user(),
        available_ingredient_ids={FLOUR, EGGS},  # milk missing entirely
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert gaps == [MILK]


def test_true_gaps_excludes_essential_covered_by_valid_substitution() -> None:
    gaps = _generator().true_gaps(
        _recipe(),
        user=_user(),
        available_ingredient_ids={FLOUR, EGGS, ALMOND_MILK},  # milk substitutable
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={MILK: [_substitution()]},
        ingredients_by_id=_catalog(),
    )
    assert gaps == []


def test_true_gaps_excludes_ingredients_already_on_hand() -> None:
    gaps = _generator().true_gaps(
        _recipe(),
        user=_user(),
        available_ingredient_ids={FLOUR, EGGS, MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert gaps == []


def test_true_gaps_never_includes_optional_ingredients() -> None:
    gaps = _generator().true_gaps(
        _recipe(),
        user=_user(),
        # strawberries (optional) missing entirely and no substitute exists.
        available_ingredient_ids={FLOUR, EGGS, MILK},
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert gaps == []


def test_true_gaps_lists_multiple_missing_essentials_in_recipe_order() -> None:
    gaps = _generator().true_gaps(
        _recipe(),
        user=_user(),
        available_ingredient_ids=set(),  # nothing on hand
        context=SubstitutionContext.GENERAL,
        candidates_by_ingredient_id={},
        ingredients_by_id=_catalog(),
    )
    assert gaps == [FLOUR, EGGS, MILK]


# --- AC2: have X of Y progress ------------------------------------------------


def test_progress_counts_across_full_ingredient_list() -> None:
    progress = ShoppingListGenerator.progress(
        _recipe(), available_ingredient_ids={FLOUR, EGGS}
    )
    assert progress.have_count == 2
    assert progress.total_count == 4  # 3 essential + 1 optional


def test_progress_is_zero_of_total_when_nothing_on_hand() -> None:
    progress = ShoppingListGenerator.progress(
        _recipe(), available_ingredient_ids=set()
    )
    assert progress.have_count == 0
    assert progress.total_count == 4
