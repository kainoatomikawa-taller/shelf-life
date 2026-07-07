"""Discover feed and per-recipe shopping list HTTP controller (§5.4).

Thin route handlers: validate input (via schemas/query params) -> call use
case -> serialize output. No business logic and no direct repository/DB
access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status

from src.application.dtos.discover_dtos import (
    AddShoppingListItemsInput,
    GenerateShoppingListInput,
    GetDiscoverFeedInput,
)
from src.domain.exceptions import DomainError, RecipeNotFoundError, UserNotFoundError
from src.interfaces.http.dependencies import (
    AddShoppingListItemsUseCaseDep,
    CurrentUserIdDep,
    GenerateShoppingListForRecipeUseCaseDep,
    GetDiscoverFeedUseCaseDep,
)
from src.interfaces.http.schemas import DiscoverRecipeCardResponse, ShoppingListResponse

router = APIRouter(prefix="/discover", tags=["discover"])


@router.get("/feed", response_model=list[DiscoverRecipeCardResponse])
async def get_discover_feed(
    current_user_id: CurrentUserIdDep,
    use_case: GetDiscoverFeedUseCaseDep,
    tab: str = Query("for_you"),
) -> list[DiscoverRecipeCardResponse]:
    try:
        outputs = await use_case.execute(
            GetDiscoverFeedInput(user_id=current_user_id, tab=tab)
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DomainError as exc:  # e.g. unknown tab
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return [DiscoverRecipeCardResponse(**asdict(o)) for o in outputs]


@router.get(
    "/recipes/{recipe_id}/shopping-list", response_model=ShoppingListResponse
)
async def generate_shopping_list(
    recipe_id: str,
    current_user_id: CurrentUserIdDep,
    use_case: GenerateShoppingListForRecipeUseCaseDep,
) -> ShoppingListResponse:
    try:
        output = await use_case.execute(
            GenerateShoppingListInput(user_id=current_user_id, recipe_id=recipe_id)
        )
    except (UserNotFoundError, RecipeNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ShoppingListResponse(**asdict(output))


@router.post(
    "/recipes/{recipe_id}/shopping-list", response_model=ShoppingListResponse
)
async def add_shopping_list_items(
    recipe_id: str,
    current_user_id: CurrentUserIdDep,
    use_case: AddShoppingListItemsUseCaseDep,
) -> ShoppingListResponse:
    try:
        output = await use_case.execute(
            AddShoppingListItemsInput(user_id=current_user_id, recipe_id=recipe_id)
        )
    except (UserNotFoundError, RecipeNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ShoppingListResponse(**asdict(output))
