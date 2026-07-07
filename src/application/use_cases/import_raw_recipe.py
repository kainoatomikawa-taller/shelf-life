"""ImportRawRecipe use case — pipeline stage 1: import.

Lands a recipe pulled from an external source into the raw-recipe staging
area, untouched and untrusted. Fails loudly on a re-import of the same
source recipe rather than silently creating a duplicate staging row.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.application.dtos.raw_recipe_dtos import ImportRawRecipeInput, RawRecipeOutput
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.domain.entities.raw_recipe import RawRecipe
from src.domain.exceptions import DuplicateRawRecipeError
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository


class ImportRawRecipeUseCase:
    """Stage 1 of the ingestion pipeline: import."""

    def __init__(self, raw_recipe_repository: RawRecipeRepository) -> None:
        self._raw_recipe_repository = raw_recipe_repository

    async def execute(self, dto: ImportRawRecipeInput) -> RawRecipeOutput:
        existing = await self._raw_recipe_repository.get_by_source(
            dto.source, dto.source_recipe_id
        )
        if existing is not None:
            raise DuplicateRawRecipeError(dto.source, dto.source_recipe_id)

        raw_recipe = RawRecipe(
            id=str(uuid.uuid4()),
            source=dto.source,
            source_recipe_id=dto.source_recipe_id,
            license=dto.license,
            raw_name=dto.raw_name,
            raw_ingredients=dto.raw_ingredients,
            raw_method=dto.raw_method,
            imported_at=datetime.now(UTC),
            raw_attribution=dto.raw_attribution,
        )
        await self._raw_recipe_repository.add(raw_recipe)

        return RawRecipeMapper.to_output(raw_recipe)
