"""Unit tests for SubstitutionEngine — the §5.5 hard-constraint-safe substitution
finder. Covers all three acceptance criteria:
1. Never substitutes across an allergy/diet hard constraint.
2. Only swaps above the confidence threshold qualify.
3. Context validity is respected and every suggestion carries a disclosure.
"""

import pytest

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.substitution import Substitution
from src.domain.entities.user import User
from src.domain.exceptions import IngredientNotFoundError
from src.domain.services.substitution_engine import SubstitutionEngine
from src.domain.value_objects.diet_type import DietType
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.soft_preferences import SoftPreferences
from src.domain.value_objects.storage_location import StorageLocation
from src.domain.value_objects.substitution_context import SubstitutionContext

MILK = "ingredient-milk"
BUTTERMILK = "ingredient-buttermilk"
ALMOND_MILK = "ingredient-almond-milk"
YOGURT = "ingredient-yogurt"


def _ingredient(id: str, allergen_tags: list[str], diet_tags: list[str]) -> Ingredient:
    return Ingredient(
        id=id,
        name=id,
        aliases=[],
        category=IngredientCategory.PERISHABLE_FRIDGE,
        default_storage_location=StorageLocation.FRIDGE,
        typical_shelf_life=ShelfLifeByStorage(fridge_days=7),
        allergen_tags=allergen_tags,
        diet_tags=diet_tags,
    )


def _catalog() -> dict[str, Ingredient]:
    return {
        MILK: _ingredient(MILK, allergen_tags=["dairy"], diet_tags=[]),
        BUTTERMILK: _ingredient(BUTTERMILK, allergen_tags=["dairy"], diet_tags=[]),
        ALMOND_MILK: _ingredient(
            ALMOND_MILK, allergen_tags=["tree_nuts"], diet_tags=["vegan"]
        ),
        YOGURT: _ingredient(YOGURT, allergen_tags=["dairy"], diet_tags=[]),
    }


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


def _engine() -> SubstitutionEngine:
    return SubstitutionEngine()


def _find(
    engine: SubstitutionEngine,
    user: User,
    candidates: list[Substitution],
    available: set[str],
    context: SubstitutionContext = SubstitutionContext.GENERAL,
    missing: str = MILK,
    threshold: float = 0.8,
) -> list:
    return engine.find_valid_substitutions(
        missing_ingredient_id=missing,
        context=context,
        user=user,
        available_ingredient_ids=available,
        candidates=candidates,
        ingredients_by_id=_catalog(),
        confidence_threshold=threshold,
    )


# --- AC1: hard-constraint safety --------------------------------------------


def test_rejects_substitution_that_contains_users_allergen() -> None:
    engine = _engine()
    user = _user(allergies=["tree_nuts"])
    candidates = [_substitution(to_ingredient_id=ALMOND_MILK)]
    result = _find(engine, user, candidates, available={ALMOND_MILK})
    assert result == []


def test_rejects_substitution_incompatible_with_users_diet() -> None:
    engine = _engine()
    user = _user(diet_type=DietType.VEGAN)
    # Yogurt has no "vegan" diet tag — must not be suggested to a vegan user.
    candidates = [_substitution(to_ingredient_id=YOGURT)]
    result = _find(engine, user, candidates, available={YOGURT})
    assert result == []


def test_allows_substitution_that_clears_both_hard_constraints() -> None:
    engine = _engine()
    user = _user(allergies=["dairy"], diet_type=DietType.VEGAN)
    candidates = [_substitution(to_ingredient_id=ALMOND_MILK)]
    result = _find(engine, user, candidates, available={ALMOND_MILK})
    assert [s.to_ingredient_id for s in result] == [ALMOND_MILK]


def test_hard_constraint_rejection_is_not_overridden_by_high_confidence() -> None:
    engine = _engine()
    user = _user(allergies=["dairy"])
    candidates = [
        _substitution(
            to_ingredient_id=BUTTERMILK,
            confidence=1.0,
            context=SubstitutionContext.GENERAL,
        )
    ]
    result = _find(engine, user, candidates, available={BUTTERMILK})
    assert result == []


# --- AC2: confidence threshold ----------------------------------------------


def test_rejects_substitution_below_confidence_threshold() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(confidence=0.5)]
    result = _find(engine, user, candidates, available={ALMOND_MILK}, threshold=0.8)
    assert result == []


def test_allows_substitution_at_exactly_the_threshold() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(confidence=0.8)]
    result = _find(engine, user, candidates, available={ALMOND_MILK}, threshold=0.8)
    assert len(result) == 1


def test_results_are_sorted_most_confident_first() -> None:
    engine = _engine()
    user = _user()
    candidates = [
        _substitution(id="a", to_ingredient_id=ALMOND_MILK, confidence=0.85),
        _substitution(id="b", to_ingredient_id=YOGURT, confidence=0.99),
    ]
    result = _find(
        engine, user, candidates, available={ALMOND_MILK, YOGURT}, threshold=0.8
    )
    assert [s.to_ingredient_id for s in result] == [YOGURT, ALMOND_MILK]


# --- AC3: context validity + disclosure -------------------------------------


def test_rejects_substitution_valid_only_for_a_different_context() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(context=SubstitutionContext.BAKING)]
    result = _find(
        engine,
        user,
        candidates,
        available={ALMOND_MILK},
        context=SubstitutionContext.SAVORY,
    )
    assert result == []


def test_general_substitution_is_valid_in_any_context() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(context=SubstitutionContext.GENERAL)]
    result = _find(
        engine,
        user,
        candidates,
        available={ALMOND_MILK},
        context=SubstitutionContext.SAVORY,
    )
    assert len(result) == 1


def test_suggestion_always_carries_a_disclosure_even_without_an_impact_note() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(impact_note=None, ratio_note=None)]
    result = _find(engine, user, candidates, available={ALMOND_MILK})
    assert result[0].disclosure
    assert "No noted impact" in result[0].disclosure


def test_suggestion_discloses_the_actual_impact_note_when_present() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(impact_note="Slightly nuttier flavor.")]
    result = _find(engine, user, candidates, available={ALMOND_MILK})
    assert result[0].disclosure == "Slightly nuttier flavor."


# --- Inventory awareness + edge cases ---------------------------------------


def test_rejects_substitution_not_in_users_inventory() -> None:
    engine = _engine()
    user = _user()
    candidates = [_substitution(to_ingredient_id=ALMOND_MILK)]
    result = _find(engine, user, candidates, available=set())
    assert result == []


def test_ignores_candidates_for_a_different_missing_ingredient() -> None:
    engine = _engine()
    user = _user()
    candidates = [
        _substitution(from_ingredient_id=YOGURT, to_ingredient_id=ALMOND_MILK)
    ]
    result = _find(engine, user, candidates, available={ALMOND_MILK}, missing=MILK)
    assert result == []


def test_raises_when_missing_ingredient_is_not_in_catalog() -> None:
    engine = _engine()
    user = _user()
    with pytest.raises(IngredientNotFoundError):
        engine.find_valid_substitutions(
            missing_ingredient_id="ingredient-unknown",
            context=SubstitutionContext.GENERAL,
            user=user,
            available_ingredient_ids=set(),
            candidates=[],
            ingredients_by_id=_catalog(),
        )
