"""SearchIngredients use case.

Powers the catalog search box on the add-item screen (§5.2 AC1): a
type-ahead lookup across ingredient names and aliases, so an aliased query
like "scallion" surfaces its canonical ingredient, "Green Onions".
"""

from __future__ import annotations

from src.application.dtos.ingredient_dtos import (
    IngredientSummaryOutput,
    SearchIngredientsInput,
)
from src.application.mappers.ingredient_mapper import IngredientMapper
from src.domain.repositories.ingredient_repository import IngredientRepository


class SearchIngredientsUseCase:
    """Search the ingredient catalog by name or alias."""

    def __init__(self, repository: IngredientRepository) -> None:
        self._repository = repository

    async def execute(
        self, dto: SearchIngredientsInput
    ) -> list[IngredientSummaryOutput]:
        if not dto.query.strip():
            return []
        ingredients = await self._repository.search(dto.query, limit=dto.limit)
        return [IngredientMapper.to_summary(i) for i in ingredients]
