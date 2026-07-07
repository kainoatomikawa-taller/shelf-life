"""Use case tests for TagRawRecipe (ingestion pipeline stage 2: tag)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.raw_recipe_dtos import (
    TaggedIngredientInput,
    TagRawRecipeInput,
)
from src.application.use_cases.tag_raw_recipe import TagRawRecipeUseCase
from src.domain.entities.raw_recipe import RawRecipe
from src.domain.exceptions import InvalidPipelineTransitionError, RawRecipeNotFoundError
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient
from tests.fakes.in_memory_raw_recipe_repository import InMemoryRawRecipeRepository

RAW_RECIPE_ID = "raw-1"


def _raw_recipe(**overrides: object) -> RawRecipe:
    defaults: dict = dict(
        id=RAW_RECIPE_ID,
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour"],
        raw_method=["Mix.", "Cook."],
        imported_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    defaults.update(overrides)
    return RawRecipe(**defaults)  # type: ignore[arg-type]


def _tag_input(**overrides: object) -> TagRawRecipeInput:
    defaults: dict = dict(
        raw_recipe_id=RAW_RECIPE_ID,
        tagged_ingredients=[
            TaggedIngredientInput(
                raw_text="2 cups flour",
                ingredient_id="ingredient-flour",
                role="essential",
            )
        ],
        difficulty="beginner",
        time_minutes=20,
        cuisine_tags=["breakfast", "easy"],
    )
    defaults.update(overrides)
    return TagRawRecipeInput(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_tags_an_imported_raw_recipe_and_advances_its_stage() -> None:
    repo = InMemoryRawRecipeRepository([_raw_recipe()])
    use_case = TagRawRecipeUseCase(repo)

    output = await use_case.execute(_tag_input())

    assert output.stage == PipelineStage.TAGGED.value
    assert output.cuisine_tags == ["breakfast", "easy"]
    assert output.difficulty == "beginner"
    assert output.time_minutes == 20
    assert output.tagged_ingredients[0].ingredient_id == "ingredient-flour"
    assert output.tagged_ingredients[0].matched is True
    persisted = await repo.get_by_id(RAW_RECIPE_ID)
    assert persisted.stage == PipelineStage.TAGGED


@pytest.mark.asyncio
async def test_unknown_raw_recipe_raises_not_found() -> None:
    repo = InMemoryRawRecipeRepository()
    use_case = TagRawRecipeUseCase(repo)

    with pytest.raises(RawRecipeNotFoundError):
        await use_case.execute(_tag_input(raw_recipe_id="ghost"))


@pytest.mark.asyncio
async def test_tagging_an_already_tagged_recipe_raises() -> None:
    already_tagged = _raw_recipe()
    already_tagged.tag(
        tagged_ingredients=[
            TaggedIngredient(
                raw_text="2 cups flour",
                ingredient_id="ingredient-flour",
                role=IngredientRole.ESSENTIAL,
            )
        ],
        difficulty=SkillLevel.BEGINNER,
        time_minutes=20,
    )
    repo = InMemoryRawRecipeRepository([already_tagged])
    use_case = TagRawRecipeUseCase(repo)

    with pytest.raises(InvalidPipelineTransitionError):
        await use_case.execute(_tag_input())
