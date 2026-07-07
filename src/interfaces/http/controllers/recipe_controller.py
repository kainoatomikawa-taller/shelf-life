"""Recipe detail HTTP controller.

Thin route handler: validate input -> call use case -> serialize output.
No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from src.application.dtos.recipe_detail_dtos import GetRecipeDetailInput
from src.domain.exceptions import RecipeNotFoundError
from src.interfaces.http.dependencies import GetRecipeDetailUseCaseDep
from src.interfaces.http.schemas import RecipeDetailResponse

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe_detail(
    recipe_id: str,
    use_case: GetRecipeDetailUseCaseDep,
) -> RecipeDetailResponse:
    try:
        output = await use_case.execute(GetRecipeDetailInput(recipe_id=recipe_id))
    except RecipeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return RecipeDetailResponse(**asdict(output))
