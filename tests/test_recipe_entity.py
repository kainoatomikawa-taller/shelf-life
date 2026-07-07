"""Unit tests for the Recipe entity and derived allergen/diet tags."""

import pytest

from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.exceptions import IngredientNotFoundError, ValidationError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_image import RecipeImage
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.storage_location import StorageLocation


def _ingredient(**overrides: object) -> Ingredient:
    defaults: dict = dict(
        id="ingredient-1",
        name="Chicken Breast",
        aliases=[],
        category=IngredientCategory.PERISHABLE_FRIDGE,
        default_storage_location=StorageLocation.FRIDGE,
        typical_shelf_life=ShelfLifeByStorage(fridge_days=3),
        allergen_tags=[],
        diet_tags=["gluten_free"],
    )
    defaults.update(overrides)
    return Ingredient(**defaults)  # type: ignore[arg-type]


def _recipe_ingredient(
    ingredient_id: str = "ingredient-1", role: IngredientRole = IngredientRole.ESSENTIAL
) -> RecipeIngredient:
    return RecipeIngredient(ingredient_id=ingredient_id, role=role)


def _recipe(**overrides: object) -> Recipe:
    defaults: dict = dict(
        id="recipe-1",
        name="Chicken Stir Fry",
        ingredients=[_recipe_ingredient()],
        steps=["Cook the chicken.", "Add vegetables."],
        time_minutes=30,
        difficulty=SkillLevel.INTERMEDIATE,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
        cuisine_tags=["Chinese"],
        flavor_tags=["Savory"],
        technique_tags=["Stir-Frying"],
        equipment_needed=["Wok"],
        popularity_score=0.8,
    )
    defaults.update(overrides)
    return Recipe(**defaults)  # type: ignore[arg-type]


def test_captures_license_and_source_attribution() -> None:
    recipe = _recipe(
        license=License.CC_BY, source_attribution="spoonacular (source id: 12345)"
    )
    assert recipe.license is License.CC_BY
    assert recipe.source_attribution == "spoonacular (source id: 12345)"


def test_rejects_invalid_license() -> None:
    with pytest.raises(ValidationError):
        _recipe(license="cc-by")  # type: ignore[arg-type]


def test_rejects_empty_source_attribution() -> None:
    with pytest.raises(ValidationError):
        _recipe(source_attribution="")


def test_image_defaults_to_none() -> None:
    assert _recipe().image is None


def test_image_can_be_set_to_a_storable_recipe_image() -> None:
    image = RecipeImage(url="https://example.com/photo.jpg", license=License.CC0)
    assert _recipe(image=image).image == image


def test_rejects_a_non_recipe_image_value() -> None:
    with pytest.raises(ValidationError):
        _recipe(image="https://example.com/photo.jpg")  # type: ignore[arg-type]


def test_flavor_profile_defaults_to_neutral() -> None:
    assert _recipe().flavor_profile == FlavorProfile()


def test_flavor_profile_can_be_set_explicitly() -> None:
    profile = FlavorProfile(sweetness=0.9, spiciness=0.1)
    assert _recipe(flavor_profile=profile).flavor_profile == profile


def test_tags_are_normalized_to_lowercase() -> None:
    recipe = _recipe()
    assert recipe.cuisine_tags == ["chinese"]
    assert recipe.flavor_tags == ["savory"]
    assert recipe.technique_tags == ["stir-frying"]
    assert recipe.equipment_needed == ["wok"]


def test_requires_at_least_one_ingredient() -> None:
    with pytest.raises(ValidationError):
        _recipe(ingredients=[])


def test_requires_at_least_one_essential_ingredient() -> None:
    with pytest.raises(ValidationError):
        _recipe(
            ingredients=[
                _recipe_ingredient("ingredient-1", IngredientRole.OPTIONAL)
            ]
        )


def test_requires_at_least_one_step() -> None:
    with pytest.raises(ValidationError):
        _recipe(steps=[])
    with pytest.raises(ValidationError):
        _recipe(steps=["   "])


def test_time_minutes_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _recipe(time_minutes=0)


def test_popularity_score_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        _recipe(popularity_score=-0.1)


def test_difficulty_must_be_a_skill_level() -> None:
    with pytest.raises(ValidationError):
        _recipe(difficulty="advanced")


def test_essential_and_optional_ingredients_are_partitioned() -> None:
    recipe = _recipe(
        ingredients=[
            _recipe_ingredient("ingredient-1", IngredientRole.ESSENTIAL),
            _recipe_ingredient("ingredient-2", IngredientRole.OPTIONAL),
        ]
    )
    assert [i.ingredient_id for i in recipe.essential_ingredients()] == [
        "ingredient-1"
    ]
    assert [i.ingredient_id for i in recipe.optional_ingredients()] == [
        "ingredient-2"
    ]


def test_derive_allergen_tags_unions_essential_and_optional() -> None:
    recipe = _recipe(
        ingredients=[
            _recipe_ingredient("ingredient-1", IngredientRole.ESSENTIAL),
            _recipe_ingredient("ingredient-2", IngredientRole.OPTIONAL),
        ]
    )
    catalog = {
        "ingredient-1": _ingredient(id="ingredient-1", allergen_tags=["dairy"]),
        "ingredient-2": _ingredient(id="ingredient-2", allergen_tags=["peanuts"]),
    }
    assert recipe.derive_allergen_tags(catalog) == ["dairy", "peanuts"]


def test_derive_diet_tags_intersects_essential_ingredients_only() -> None:
    recipe = _recipe(
        ingredients=[
            _recipe_ingredient("ingredient-1", IngredientRole.ESSENTIAL),
            _recipe_ingredient("ingredient-2", IngredientRole.ESSENTIAL),
            _recipe_ingredient("ingredient-3", IngredientRole.OPTIONAL),
        ]
    )
    catalog = {
        "ingredient-1": _ingredient(
            id="ingredient-1", diet_tags=["vegan", "vegetarian"]
        ),
        "ingredient-2": _ingredient(id="ingredient-2", diet_tags=["vegan"]),
        # Optional and non-vegan — must not strip the vegan tag.
        "ingredient-3": _ingredient(id="ingredient-3", diet_tags=[]),
    }
    assert recipe.derive_diet_tags(catalog) == ["vegan"]


def test_derive_allergen_tags_raises_when_ingredient_missing_from_catalog() -> None:
    recipe = _recipe()
    with pytest.raises(IngredientNotFoundError):
        recipe.derive_allergen_tags({})


def test_derive_diet_tags_raises_when_ingredient_missing_from_catalog() -> None:
    recipe = _recipe()
    with pytest.raises(IngredientNotFoundError):
        recipe.derive_diet_tags({})


def test_recipe_ingredient_requires_ingredient_id() -> None:
    with pytest.raises(ValidationError):
        RecipeIngredient(ingredient_id="", role=IngredientRole.ESSENTIAL)


def test_recipe_ingredient_is_essential_reflects_role() -> None:
    assert _recipe_ingredient(role=IngredientRole.ESSENTIAL).is_essential is True
    assert _recipe_ingredient(role=IngredientRole.OPTIONAL).is_essential is False


def test_record_rating_increases_popularity_score() -> None:
    recipe = _recipe(popularity_score=0.5)
    recipe.record_rating(stars=5.0)
    assert recipe.popularity_score > 0.5


def test_record_rating_increases_popularity_more_for_higher_stars() -> None:
    low_rated = _recipe(popularity_score=0.5)
    low_rated.record_rating(stars=1.0)

    high_rated = _recipe(popularity_score=0.5)
    high_rated.record_rating(stars=5.0)

    assert high_rated.popularity_score > low_rated.popularity_score


def test_record_rating_rejects_out_of_range_stars() -> None:
    recipe = _recipe()
    with pytest.raises(ValidationError):
        recipe.record_rating(stars=6.0)


def test_recipe_equality_is_by_id() -> None:
    assert _recipe(id="recipe-1") == _recipe(id="recipe-1", name="Different Name")
    assert _recipe(id="recipe-1") != _recipe(id="recipe-2")
