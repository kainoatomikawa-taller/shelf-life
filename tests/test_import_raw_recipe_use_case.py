"""Use case tests for ImportRawRecipe (ingestion pipeline stage 1: import)."""

import pytest

from src.application.dtos.raw_recipe_dtos import ImportRawRecipeInput
from src.application.use_cases.import_raw_recipe import ImportRawRecipeUseCase
from src.domain.exceptions import DuplicateRawRecipeError
from src.domain.value_objects.pipeline_stage import PipelineStage
from tests.fakes.in_memory_raw_recipe_repository import InMemoryRawRecipeRepository


def _input(**overrides: object) -> ImportRawRecipeInput:
    defaults: dict = dict(
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour", "2 eggs"],
        raw_method=["Mix.", "Cook."],
    )
    defaults.update(overrides)
    return ImportRawRecipeInput(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_stages_a_new_raw_recipe_at_the_imported_stage() -> None:
    repo = InMemoryRawRecipeRepository()
    use_case = ImportRawRecipeUseCase(repo)

    output = await use_case.execute(_input())

    assert output.stage == PipelineStage.IMPORTED.value
    assert output.source == "spoonacular"
    assert output.source_recipe_id == "12345"
    persisted = await repo.get_by_id(output.id)
    assert persisted is not None


@pytest.mark.asyncio
async def test_reimporting_the_same_source_recipe_raises() -> None:
    repo = InMemoryRawRecipeRepository()
    use_case = ImportRawRecipeUseCase(repo)
    await use_case.execute(_input())

    with pytest.raises(DuplicateRawRecipeError):
        await use_case.execute(_input())


@pytest.mark.asyncio
async def test_same_source_recipe_id_from_a_different_source_is_allowed() -> None:
    repo = InMemoryRawRecipeRepository()
    use_case = ImportRawRecipeUseCase(repo)
    await use_case.execute(_input(source="spoonacular"))

    output = await use_case.execute(_input(source="edamam"))
    assert output.source == "edamam"
