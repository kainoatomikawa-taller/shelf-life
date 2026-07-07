"""Post-cook rating HTTP controller (§5.6).

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status

from src.application.dtos.rating_dtos import (
    DecrementRecipeIngredientsInput,
    GetUserRatingsInput,
    SubmitRatingInput,
)
from src.domain.exceptions import (
    IngredientNotFoundError,
    RecipeNotFoundError,
    UserNotFoundError,
)
from src.interfaces.http.dependencies import (
    DecrementRecipeIngredientsUseCaseDep,
    GetUserRatingsUseCaseDep,
    SubmitRatingUseCaseDep,
)
from src.interfaces.http.schemas import (
    DecrementRecipeIngredientsRequest,
    InventoryItemResponse,
    RatingResponse,
    SubmitRatingRequest,
    UserRatingResponse,
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.get("", response_model=list[UserRatingResponse])
async def get_user_ratings(
    use_case: GetUserRatingsUseCaseDep,
    user_id: str = Query(..., min_length=1),
) -> list[UserRatingResponse]:
    """Every rating the user has recorded, most recent first — backs the
    session-launch auto-load."""
    try:
        outputs = await use_case.execute(GetUserRatingsInput(user_id=user_id))
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return [UserRatingResponse(**asdict(o)) for o in outputs]


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def submit_rating(
    body: SubmitRatingRequest, use_case: SubmitRatingUseCaseDep
) -> RatingResponse:
    """Star/thumb rating plus optional quick tags (AC1). Surfaces which
    ingredients are eligible for the optional stock decrement without
    applying it (AC2)."""
    try:
        output = await use_case.execute(
            SubmitRatingInput(
                user_id=body.user_id,
                recipe_id=body.recipe_id,
                stars=body.stars,
                quick_tags=body.quick_tags,
            )
        )
    except (UserNotFoundError, RecipeNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return RatingResponse(**asdict(output))


@router.post("/decrement-stock", response_model=list[InventoryItemResponse])
async def decrement_recipe_ingredients(
    body: DecrementRecipeIngredientsRequest,
    use_case: DecrementRecipeIngredientsUseCaseDep,
) -> list[InventoryItemResponse]:
    """Opt-in application of the stock decrement the rating prompt offered
    (AC2/AC3) — only reachable via an explicit call, never automatic."""
    try:
        outputs = await use_case.execute(
            DecrementRecipeIngredientsInput(
                user_id=body.user_id, recipe_id=body.recipe_id
            )
        )
    except (UserNotFoundError, RecipeNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return [InventoryItemResponse(**asdict(o)) for o in outputs]
