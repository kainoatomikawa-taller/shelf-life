"""Use case tests for GetRecipeDetail."""

import pytest

from src.application.dtos.recipe_detail_dtos import GetRecipeDetailInput
from src.application.use_cases.get_recipe_detail import GetRecipeDetailUseCase
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.recipe import Recipe
from src.domain.exceptions import RecipeNotFoundError
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.storage_location import StorageLocation
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_recipe_repository import InMemoryRecipeRepository

FLOUR = "ingredient-flour"
EGGS = "ingredient-eggs"
MILK = "ingredient-milk"

RECIPE_ID = "recipe-pancakes"


def _ingredient(id: str, name: str) -> Ingredient:
    return Ingredient(
        id=id,
        name=name,
        aliases=[],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=[],
        diet_tags=[],
    )


def _recipe() -> Recipe:
    return Recipe(
        id=RECIPE_ID,
        name="Pancakes",
        ingredients=[
            RecipeIngredient(FLOUR, IngredientRole.ESSENTIAL),
            RecipeIngredient(EGGS, IngredientRole.ESSENTIAL),
            RecipeIngredient(MILK, IngredientRole.OPTIONAL),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty=SkillLevel.BEGINNER,
        license=License.SELF_AUTHORED,
        source_attribution="Test fixture",
        cuisine_tags=["american"],
    )


async def _build_use_case(recipes: list[Recipe]) -> GetRecipeDetailUseCase:
    ingredient_repo = InMemoryIngredientRepository()
    for ingredient in [
        _ingredient(FLOUR, "Flour"),
        _ingredient(EGGS, "Eggs"),
        _ingredient(MILK, "Milk"),
    ]:
        await ingredient_repo.add(ingredient)

    return GetRecipeDetailUseCase(
        recipe_repository=InMemoryRecipeRepository(recipes),
        ingredient_repository=ingredient_repo,
    )


@pytest.mark.asyncio
async def test_returns_full_ingredient_list_time_and_steps() -> None:
    use_case = await _build_use_case([_recipe()])
    output = await use_case.execute(GetRecipeDetailInput(recipe_id=RECIPE_ID))

    assert output.id == RECIPE_ID
    assert output.name == "Pancakes"
    assert output.time_minutes == 20
    assert output.difficulty == "beginner"
    assert output.cuisine_tags == ["american"]
    assert output.steps == ["Mix.", "Cook."]
    assert [(i.ingredient_name, i.role) for i in output.ingredients] == [
        ("Flour", "essential"),
        ("Eggs", "essential"),
        ("Milk", "optional"),
    ]


@pytest.mark.asyncio
async def test_unknown_recipe_raises_not_found() -> None:
    use_case = await _build_use_case([])
    with pytest.raises(RecipeNotFoundError):
        await use_case.execute(GetRecipeDetailInput(recipe_id="ghost-recipe"))
