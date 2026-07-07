"""Shopping List tab HTTP controller (§5.7).

Thin route handlers: validate input (via schemas/query params) -> call use
case -> serialize output. No business logic and no direct repository/DB
access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from src.application.dtos.inventory_item_dtos import InventoryItemOutput
from src.application.dtos.shopping_list_dtos import (
    AddPurchasesToKitchenInput,
    CheckShoppingListItemInput,
    GetShoppingListInput,
)
from src.domain.exceptions import (
    DomainError,
    IngredientNotFoundError,
    ShoppingListItemNotFoundError,
    UserNotFoundError,
)
from src.interfaces.http.dependencies import (
    AddPurchasesToKitchenUseCaseDep,
    CheckShoppingListItemUseCaseDep,
    CurrentUserIdDep,
    GetShoppingListUseCaseDep,
)
from src.interfaces.http.schemas import (
    AddPurchasesToKitchenRequest,
    CheckShoppingListItemRequest,
    InventoryItemResponse,
    ShoppingListEntryResponse,
)

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


@router.get("", response_model=list[ShoppingListEntryResponse])
async def get_shopping_list(
    current_user_id: CurrentUserIdDep,
    use_case: GetShoppingListUseCaseDep,
) -> list[ShoppingListEntryResponse]:
    """Aggregates Discover-sourced items with Low/Out inventory flags,
    merging duplicates (AC1)."""
    try:
        outputs = await use_case.execute(
            GetShoppingListInput(user_id=current_user_id)
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return [ShoppingListEntryResponse(**asdict(o)) for o in outputs]


@router.patch("/{item_id}/checked", response_model=ShoppingListEntryResponse)
async def check_shopping_list_item(
    item_id: str,
    body: CheckShoppingListItemRequest,
    use_case: CheckShoppingListItemUseCaseDep,
) -> ShoppingListEntryResponse:
    """Check off (or uncheck) an item while shopping (AC2)."""
    try:
        output = await use_case.execute(
            CheckShoppingListItemInput(item_id=item_id, checked=body.checked)
        )
    except ShoppingListItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return ShoppingListEntryResponse(**asdict(output))


@router.post("/purchases", response_model=list[InventoryItemResponse])
async def add_purchases_to_kitchen(
    body: AddPurchasesToKitchenRequest,
    current_user_id: CurrentUserIdDep,
    use_case: AddPurchasesToKitchenUseCaseDep,
) -> list[InventoryItemResponse]:
    """On trip complete, adds every checked-off item to the Kitchen,
    dated today by default (AC3)."""
    try:
        outputs: list[InventoryItemOutput] = await use_case.execute(
            AddPurchasesToKitchenInput(
                user_id=current_user_id, purchase_date=body.purchase_date
            )
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (IngredientNotFoundError, DomainError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return [InventoryItemResponse(**asdict(o)) for o in outputs]
