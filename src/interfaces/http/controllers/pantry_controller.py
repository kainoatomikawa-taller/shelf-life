"""Pantry item HTTP controller.

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Response, status

from src.application.dtos.pantry_item_dtos import (
    AddPantryItemInput,
    ConsumePantryItemInput,
    ListPantryItemsInput,
)
from src.interfaces.http.dependencies import (
    AddUseCaseDep,
    ConsumeUseCaseDep,
    ListUseCaseDep,
)
from src.interfaces.http.schemas import (
    AddPantryItemRequest,
    ConsumePantryItemRequest,
    PantryItemResponse,
)

router = APIRouter(prefix="/pantry-items", tags=["pantry-items"])


@router.post(
    "",
    response_model=PantryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_pantry_item(
    body: AddPantryItemRequest, use_case: AddUseCaseDep
) -> PantryItemResponse:
    try:
        output = await use_case.execute(
            AddPantryItemInput(
                owner_id=body.owner_id,
                name=body.name,
                amount=body.amount,
                unit=body.unit,
                expiration_date=body.expiration_date,
            )
        )
    except ValueError as exc:  # unknown unit / invalid value object
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return PantryItemResponse(**asdict(output))


@router.get("", response_model=list[PantryItemResponse])
async def list_pantry_items(
    owner_id: str, use_case: ListUseCaseDep
) -> list[PantryItemResponse]:
    outputs = await use_case.execute(ListPantryItemsInput(owner_id=owner_id))
    return [PantryItemResponse(**asdict(o)) for o in outputs]


@router.post("/{item_id}/consume")
async def consume_pantry_item(
    item_id: str,
    body: ConsumePantryItemRequest,
    use_case: ConsumeUseCaseDep,
) -> Response | PantryItemResponse:
    from src.domain.exceptions import PantryItemNotFoundError  # local: mapping only

    try:
        output = await use_case.execute(
            ConsumePantryItemInput(
                item_id=item_id, amount=body.amount, unit=body.unit
            )
        )
    except PantryItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if output is None:
        # Item fully consumed and removed.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return PantryItemResponse(**asdict(output))
