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
    RemoveInventoryItemInput,
    UpdateInventoryItemDatesInput,
    UpdateQuantityStateInput,
)
from src.domain.exceptions import (
    DomainError,
    IngredientNotFoundError,
    InventoryItemNotFoundError,
)
from src.interfaces.http.dependencies import (
    AddInventoryItemUseCaseDep,
    CurrentUserIdDep,
    ListInventoryItemsUseCaseDep,
    RemoveInventoryItemUseCaseDep,
    UpdateInventoryItemDatesUseCaseDep,
    UpdateInventoryItemQuantityStateUseCaseDep,
)
from src.interfaces.http.schemas import (
    AddInventoryItemRequest,
    InventoryItemResponse,
    UpdateInventoryItemDatesRequest,
    UpdateQuantityStateRequest,
)

router = APIRouter(prefix="/inventory-items", tags=["inventory-items"])


@router.post(
    "",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_inventory_item(
    body: AddInventoryItemRequest,
    current_user_id: CurrentUserIdDep,
    use_case: AddInventoryItemUseCaseDep,
) -> InventoryItemResponse:
    try:
        output = await use_case.execute(
            AddInventoryItemInput(
                user_id=current_user_id,
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
    current_user_id: CurrentUserIdDep, use_case: ListInventoryItemsUseCaseDep
) -> list[InventoryItemResponse]:
    outputs = await use_case.execute(ListInventoryItemsInput(user_id=current_user_id))
    return [InventoryItemResponse(**asdict(o)) for o in outputs]


@router.patch("/{item_id}/quantity-state", response_model=InventoryItemResponse)
async def update_quantity_state(
    item_id: str,
    body: UpdateQuantityStateRequest,
    use_case: UpdateInventoryItemQuantityStateUseCaseDep,
) -> InventoryItemResponse:
    """One-tap Mark Low / Mark Out (and undo, Mark In) (§5.2 AC2)."""
    try:
        output = await use_case.execute(
            UpdateQuantityStateInput(
                item_id=item_id, quantity_state=body.quantity_state
            )
        )
    except InventoryItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (ValueError, DomainError) as exc:  # unknown enum value
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return InventoryItemResponse(**asdict(output))


@router.patch("/{item_id}/dates", response_model=InventoryItemResponse)
async def update_dates(
    item_id: str,
    body: UpdateInventoryItemDatesRequest,
    use_case: UpdateInventoryItemDatesUseCaseDep,
) -> InventoryItemResponse:
    """Edit-dates quick action (§5.2): corrects the purchase/package dates."""
    try:
        output = await use_case.execute(
            UpdateInventoryItemDatesInput(
                item_id=item_id,
                purchase_date=body.purchase_date,
                printed_package_date=body.printed_package_date,
            )
        )
    except InventoryItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DomainError as exc:  # e.g. no shelf life known for this storage
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return InventoryItemResponse(**asdict(output))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_inventory_item(
    item_id: str, use_case: RemoveInventoryItemUseCaseDep
) -> None:
    """Used-it-up / delete quick actions (§5.2 AC2): both remove the item."""
    try:
        await use_case.execute(RemoveInventoryItemInput(item_id=item_id))
    except InventoryItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
