"""Use case tests for ReviewRawRecipe (ingestion pipeline stage 3: review)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.raw_recipe_dtos import ReviewRawRecipeInput
from src.application.use_cases.review_raw_recipe import ReviewRawRecipeUseCase
from src.domain.entities.raw_recipe import RawRecipe
from src.domain.exceptions import RawRecipeNotFoundError, ValidationError
from src.domain.value_objects.pipeline_stage import PipelineStage
from tests.fakes.in_memory_raw_recipe_repository import InMemoryRawRecipeRepository

RAW_RECIPE_ID = "raw-1"


def _tagged_raw_recipe() -> RawRecipe:
    raw_recipe = RawRecipe(
        id=RAW_RECIPE_ID,
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour"],
        raw_method=["Mix.", "Cook."],
        imported_at=datetime(2026, 7, 6, tzinfo=UTC),
    )
    raw_recipe.tag(["breakfast"])
    return raw_recipe


@pytest.mark.asyncio
async def test_approving_advances_tagged_to_approved() -> None:
    repo = InMemoryRawRecipeRepository([_tagged_raw_recipe()])
    use_case = ReviewRawRecipeUseCase(repo)

    output = await use_case.execute(
        ReviewRawRecipeInput(raw_recipe_id=RAW_RECIPE_ID, approve=True, notes="Good.")
    )

    assert output.stage == PipelineStage.APPROVED.value
    assert output.review_notes == "Good."


@pytest.mark.asyncio
async def test_rejecting_advances_tagged_to_rejected_with_a_reason() -> None:
    repo = InMemoryRawRecipeRepository([_tagged_raw_recipe()])
    use_case = ReviewRawRecipeUseCase(repo)

    output = await use_case.execute(
        ReviewRawRecipeInput(
            raw_recipe_id=RAW_RECIPE_ID, approve=False, notes="Duplicate recipe."
        )
    )

    assert output.stage == PipelineStage.REJECTED.value
    assert output.rejected_reason == "Duplicate recipe."


@pytest.mark.asyncio
async def test_rejecting_without_a_reason_raises() -> None:
    repo = InMemoryRawRecipeRepository([_tagged_raw_recipe()])
    use_case = ReviewRawRecipeUseCase(repo)

    with pytest.raises(ValidationError):
        await use_case.execute(
            ReviewRawRecipeInput(raw_recipe_id=RAW_RECIPE_ID, approve=False)
        )


@pytest.mark.asyncio
async def test_unknown_raw_recipe_raises_not_found() -> None:
    repo = InMemoryRawRecipeRepository()
    use_case = ReviewRawRecipeUseCase(repo)

    with pytest.raises(RawRecipeNotFoundError):
        await use_case.execute(
            ReviewRawRecipeInput(raw_recipe_id="ghost", approve=True)
        )
