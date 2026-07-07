"""Use case tests for TagStagedRecipesWithLlm — the one-time LLM tagging
batch job (§8 AC1-4)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.recipe_tagging_dtos import (
    LlmTaggedIngredient,
    RecipeTaggingFailure,
    RecipeTaggingResult,
)
from src.application.use_cases.tag_staged_recipes_with_llm import (
    TagStagedRecipesWithLlmUseCase,
)
from src.domain.entities.ingredient import Ingredient
from src.domain.entities.raw_recipe import RawRecipe
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.storage_location import StorageLocation
from src.domain.value_objects.tagged_ingredient import TaggedIngredient
from tests.fakes.fake_recipe_tagging_port import FakeRecipeTaggingPort
from tests.fakes.in_memory_ingredient_repository import InMemoryIngredientRepository
from tests.fakes.in_memory_raw_recipe_repository import InMemoryRawRecipeRepository

IMPORTED_AT = datetime(2026, 7, 6, tzinfo=UTC)


def _flour_ingredient() -> Ingredient:
    return Ingredient(
        id="ingredient-flour",
        name="All-Purpose Flour",
        aliases=["flour"],
        category=IngredientCategory.PANTRY,
        default_storage_location=StorageLocation.PANTRY,
        typical_shelf_life=ShelfLifeByStorage(pantry_days=365),
        allergen_tags=["gluten"],
        diet_tags=["vegan", "vegetarian"],
    )


def _raw_recipe(raw_recipe_id: str, raw_ingredients: list[str]) -> RawRecipe:
    return RawRecipe(
        id=raw_recipe_id,
        source="spoonacular",
        source_recipe_id=raw_recipe_id,
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=raw_ingredients,
        raw_method=["Mix.", "Cook."],
        imported_at=IMPORTED_AT,
    )


@pytest.mark.asyncio
async def test_tags_an_imported_recipe_and_maps_ingredients_to_the_catalog() -> None:
    raw_recipe_repo = InMemoryRawRecipeRepository(
        [_raw_recipe("raw-1", ["2 cups flour"])]
    )
    ingredient_repo = InMemoryIngredientRepository()
    await ingredient_repo.add(_flour_ingredient())
    port = FakeRecipeTaggingPort(
        {
            "raw-1": RecipeTaggingResult(
                raw_recipe_id="raw-1",
                cuisine_tags=["american"],
                flavor_tags=["sweet"],
                technique_tags=["griddling"],
                difficulty="beginner",
                time_minutes=20,
                ingredients=[
                    LlmTaggedIngredient(
                        raw_text="2 cups flour",
                        catalog_name="flour",
                        role="essential",
                    )
                ],
            )
        }
    )
    use_case = TagStagedRecipesWithLlmUseCase(raw_recipe_repo, ingredient_repo, port)

    output = await use_case.execute()

    assert len(output.tagged) == 1
    tagged = output.tagged[0]
    assert tagged.stage == PipelineStage.TAGGED.value
    assert tagged.cuisine_tags == ["american"]
    assert tagged.difficulty == "beginner"
    assert tagged.time_minutes == 20
    assert tagged.tagged_ingredients[0].ingredient_id == "ingredient-flour"
    assert tagged.tagged_ingredients[0].matched is True
    assert output.failed == []

    persisted = await raw_recipe_repo.get_by_id("raw-1")
    assert persisted.stage == PipelineStage.TAGGED


@pytest.mark.asyncio
async def test_flags_ingredients_with_no_catalog_match_instead_of_guessing() -> None:
    raw_recipe_repo = InMemoryRawRecipeRepository(
        [_raw_recipe("raw-1", ["1 tbsp fairy dust"])]
    )
    ingredient_repo = InMemoryIngredientRepository()
    port = FakeRecipeTaggingPort(
        {
            "raw-1": RecipeTaggingResult(
                raw_recipe_id="raw-1",
                cuisine_tags=[],
                flavor_tags=[],
                technique_tags=[],
                difficulty="beginner",
                time_minutes=10,
                ingredients=[
                    LlmTaggedIngredient(
                        raw_text="1 tbsp fairy dust",
                        catalog_name="fairy dust",
                        role="essential",
                    )
                ],
            )
        }
    )
    use_case = TagStagedRecipesWithLlmUseCase(raw_recipe_repo, ingredient_repo, port)

    output = await use_case.execute()

    assert len(output.tagged) == 1
    ingredient = output.tagged[0].tagged_ingredients[0]
    assert ingredient.ingredient_id is None
    assert ingredient.matched is False


@pytest.mark.asyncio
async def test_a_failed_recipe_does_not_block_the_rest_of_the_batch() -> None:
    raw_recipe_repo = InMemoryRawRecipeRepository(
        [
            _raw_recipe("raw-1", ["2 cups flour"]),
            _raw_recipe("raw-2", ["3 eggs"]),
        ]
    )
    ingredient_repo = InMemoryIngredientRepository()
    await ingredient_repo.add(_flour_ingredient())
    port = FakeRecipeTaggingPort(
        {
            "raw-1": RecipeTaggingResult(
                raw_recipe_id="raw-1",
                cuisine_tags=[],
                flavor_tags=[],
                technique_tags=[],
                difficulty="beginner",
                time_minutes=20,
                ingredients=[
                    LlmTaggedIngredient(
                        raw_text="2 cups flour",
                        catalog_name="flour",
                        role="essential",
                    )
                ],
            ),
            "raw-2": RecipeTaggingFailure(
                raw_recipe_id="raw-2", reason="batch result: errored"
            ),
        }
    )
    use_case = TagStagedRecipesWithLlmUseCase(raw_recipe_repo, ingredient_repo, port)

    output = await use_case.execute()

    assert [r.id for r in output.tagged] == ["raw-1"]
    assert len(output.failed) == 1
    assert output.failed[0].raw_recipe_id == "raw-2"

    untouched = await raw_recipe_repo.get_by_id("raw-2")
    assert untouched.stage == PipelineStage.IMPORTED


@pytest.mark.asyncio
async def test_only_imported_stage_recipes_are_submitted_to_the_llm() -> None:
    already_tagged = _raw_recipe("raw-1", ["2 cups flour"])
    already_tagged.tag(
        tagged_ingredients=[
            TaggedIngredient(
                raw_text="2 cups flour",
                ingredient_id=None,
                role=IngredientRole.ESSENTIAL,
            )
        ],
        difficulty=SkillLevel.BEGINNER,
        time_minutes=20,
    )
    raw_recipe_repo = InMemoryRawRecipeRepository(
        [already_tagged, _raw_recipe("raw-2", ["3 eggs"])]
    )
    ingredient_repo = InMemoryIngredientRepository()
    port = FakeRecipeTaggingPort(
        {
            "raw-2": RecipeTaggingResult(
                raw_recipe_id="raw-2",
                cuisine_tags=[],
                flavor_tags=[],
                technique_tags=[],
                difficulty="beginner",
                time_minutes=5,
                ingredients=[
                    LlmTaggedIngredient(
                        raw_text="3 eggs", catalog_name=None, role="essential"
                    )
                ],
            )
        }
    )
    use_case = TagStagedRecipesWithLlmUseCase(raw_recipe_repo, ingredient_repo, port)

    await use_case.execute()

    assert [r.raw_recipe_id for r in port.requested] == ["raw-2"]


@pytest.mark.asyncio
async def test_no_imported_recipes_short_circuits_without_calling_the_llm() -> None:
    raw_recipe_repo = InMemoryRawRecipeRepository()
    ingredient_repo = InMemoryIngredientRepository()
    port = FakeRecipeTaggingPort({})
    use_case = TagStagedRecipesWithLlmUseCase(raw_recipe_repo, ingredient_repo, port)

    output = await use_case.execute()

    assert output.tagged == []
    assert output.failed == []
    assert port.requested == []
