"""Cook Now feed HTTP controller (§5.3).

Thin route handler: validate input (via schemas/query params) -> call use
case -> serialize output. No business logic and no direct repository/DB
access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status

from src.application.dtos.cook_now_dtos import GetCookNowFeedInput
from src.domain.exceptions import DomainError, UserNotFoundError
from src.interfaces.http.dependencies import GetCookNowFeedUseCaseDep
from src.interfaces.http.schemas import RecipeCardResponse

router = APIRouter(prefix="/cook-now", tags=["cook-now"])


@router.get("/feed", response_model=list[RecipeCardResponse])
async def get_cook_now_feed(
    use_case: GetCookNowFeedUseCaseDep,
    user_id: str = Query(..., min_length=1),
    tab: str = Query("for_you"),
) -> list[RecipeCardResponse]:
    try:
        outputs = await use_case.execute(
            GetCookNowFeedInput(user_id=user_id, tab=tab)
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DomainError as exc:  # e.g. unknown tab
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return [RecipeCardResponse(**asdict(o)) for o in outputs]
