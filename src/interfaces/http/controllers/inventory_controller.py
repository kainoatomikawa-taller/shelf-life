"""Inventory item HTTP controller.

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from src.application.dtos.inventory_item_dtos import (
    AddInventoryItemInput,
    ListInventoryItemsInput,
)
from src.domain.exceptions import DomainError, IngredientNotFoundError
from src.interfaces.http.dependencies import (
    AddInventoryItemUseCaseDep,
    ListInventoryItemsUseCaseDep,
)
from src.interfaces.http.schemas import (
    AddInventoryItemRequest,
    InventoryItemResponse,
)

router = APIRouter(prefix="/inventory-items", tags=["inventory-items"])


@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_inventory_item(
    body: AddInventoryItemRequest, use_case: AddInventoryItemUseCaseDep
) -> InventoryItemResponse:
    try:
        output = await use_case.execute(
            AddInventoryItemInput(
                user_id=body.user_id,
                ingredient_id=body.ingredient_id,
                quantity_state=body.quantity_state,
                storage_location=body.storage_location,
                purchase_date=body.purchase_date,
                printed_package_date=body.printed_package_date,
                is_frozen=body.is_frozen,
                notes=body.notes,
            )
        )
    except IngredientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (ValueError, DomainError) as exc:  # unknown enum value / invalid state
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return InventoryItemResponse(**asdict(output))


@router.get("", response_model=list[InventoryItemResponse])
async def list_inventory_items(
    user_id: str, use_case: ListInventoryItemsUseCaseDep
) -> list[InventoryItemResponse]:
    outputs = await use_case.execute(ListInventoryItemsInput(user_id=user_id))
    return [InventoryItemResponse(**asdict(o)) for o in outputs]
