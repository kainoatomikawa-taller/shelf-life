"""Ingredient catalog HTTP controller.

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query

from src.application.dtos.ingredient_dtos import SearchIngredientsInput
from src.interfaces.http.dependencies import SearchIngredientsUseCaseDep
from src.interfaces.http.schemas import IngredientSummaryResponse

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/ingredients", response_model=list[IngredientSummaryResponse])
async def search_ingredients(
    use_case: SearchIngredientsUseCaseDep,
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
) -> list[IngredientSummaryResponse]:
    outputs = await use_case.execute(
        SearchIngredientsInput(query=query, limit=limit)
    )
    return [IngredientSummaryResponse(**asdict(o)) for o in outputs]
