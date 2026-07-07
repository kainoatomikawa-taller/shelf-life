"""Use case tests for PublishRawRecipe (ingestion pipeline stage 4: publish)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.raw_recipe_dtos import (
    PublishRawRecipeInput,
    PublishRecipeIngredientInput,
)
from src.application.use_cases.publish_raw_recipe import PublishRawRecipeUseCase
from src.domain.entities.raw_recipe import RawRecipe
from src.domain.exceptions import InvalidPipelineTransitionError, RawRecipeNotFoundError
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient
from tests.fakes.in_memory_raw_recipe_repository import InMemoryRawRecipeRepository
from tests.fakes.in_memory_recipe_repository import InMemoryRecipeRepository

RAW_RECIPE_ID = "raw-1"
RECIPE_ID = "recipe-1"


def _approved_raw_recipe() -> RawRecipe:
    raw_recipe = RawRecipe(
        id=RAW_RECIPE_ID,
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour", "2 eggs"],
        raw_method=["Mix.", "Cook."],
        imported_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    raw_recipe.tag(
        tagged_ingredients=[
            TaggedIngredient(
                raw_text="2 cups flour",
                ingredient_id="ingredient-flour",
                role=IngredientRole.ESSENTIAL,
            ),
            TaggedIngredient(
                raw_text="2 eggs",
                ingredient_id="ingredient-eggs",
                role=IngredientRole.ESSENTIAL,
            ),
        ],
        difficulty=SkillLevel.BEGINNER,
        time_minutes=20,
        cuisine_tags=["breakfast"],
    )
    raw_recipe.approve()
    return raw_recipe


def _publish_input(**overrides: object) -> PublishRawRecipeInput:
    defaults: dict = dict(
        raw_recipe_id=RAW_RECIPE_ID,
        recipe_id=RECIPE_ID,
        name="Grandma's Pancakes",
        ingredients=[
            PublishRecipeIngredientInput("ingredient-flour", "essential"),
            PublishRecipeIngredientInput("ingredient-eggs", "essential"),
        ],
        steps=["Mix.", "Cook."],
        time_minutes=20,
        difficulty="beginner",
    )
    defaults.update(overrides)
    return PublishRawRecipeInput(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_publishes_an_approved_raw_recipe_into_the_recipe_catalog() -> None:
    raw_repo = InMemoryRawRecipeRepository([_approved_raw_recipe()])
    recipe_repo = InMemoryRecipeRepository()
    use_case = PublishRawRecipeUseCase(raw_repo, recipe_repo)

    output = await use_case.execute(_publish_input())

    assert output.stage == PipelineStage.PUBLISHED.value
    assert output.published_recipe_id == RECIPE_ID

    published = await recipe_repo.get_by_id(RECIPE_ID)
    assert published is not None
    assert published.name == "Grandma's Pancakes"

    raw_recipe = await raw_repo.get_by_id(RAW_RECIPE_ID)
    assert raw_recipe.stage == PipelineStage.PUBLISHED
    assert raw_recipe.published_recipe_id == RECIPE_ID


@pytest.mark.asyncio
async def test_publishing_a_raw_recipe_that_was_never_approved_raises() -> None:
    unapproved = RawRecipe(
        id=RAW_RECIPE_ID,
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour"],
        raw_method=["Mix.", "Cook."],
        imported_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    raw_repo = InMemoryRawRecipeRepository([unapproved])
    recipe_repo = InMemoryRecipeRepository()
    use_case = PublishRawRecipeUseCase(raw_repo, recipe_repo)

    with pytest.raises(InvalidPipelineTransitionError):
        await use_case.execute(_publish_input())

    assert await recipe_repo.get_by_id(RECIPE_ID) is None


@pytest.mark.asyncio
async def test_unknown_raw_recipe_raises_not_found() -> None:
    raw_repo = InMemoryRawRecipeRepository()
    recipe_repo = InMemoryRecipeRepository()
    use_case = PublishRawRecipeUseCase(raw_repo, recipe_repo)

    with pytest.raises(RawRecipeNotFoundError):
        await use_case.execute(_publish_input(raw_recipe_id="ghost"))
