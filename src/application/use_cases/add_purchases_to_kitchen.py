"""AddPurchasesToKitchen use case (§5.7 AC3).

The Shopping List tab's loop-closer: on "trip complete," converts every
item the user checked off while shopping into a Kitchen inventory item —
dated today by default — then removes it from the shopping list, since
it's no longer something to buy.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from src.application.dtos.inventory_item_dtos import InventoryItemOutput
from src.application.dtos.shopping_list_dtos import AddPurchasesToKitchenInput
from src.application.mappers.inventory_item_mapper import InventoryItemMapper
from src.domain.entities.inventory_item import InventoryItem
from src.domain.exceptions import IngredientNotFoundError, UserNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.quantity_state import QuantityState


class AddPurchasesToKitchenUseCase:
    """Turn every checked-off shopping list item into a Kitchen inventory
    item and clear it from the shopping list."""

    def __init__(
        self,
        shopping_list_item_repository: ShoppingListItemRepository,
        inventory_item_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
        user_repository: UserRepository,
    ) -> None:
        self._shopping_list_item_repository = shopping_list_item_repository
        self._inventory_item_repository = inventory_item_repository
        self._ingredient_repository = ingredient_repository
        self._user_repository = user_repository

    async def execute(
        self, dto: AddPurchasesToKitchenInput
    ) -> list[InventoryItemOutput]:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        purchase_date = dto.purchase_date or date.today()
        today = date.today()
        now = datetime.now(UTC)

        items = await self._shopping_list_item_repository.list_by_user(dto.user_id)
        checked_items = [item for item in items if item.checked]

        added: list[InventoryItemOutput] = []
        for item in checked_items:
            ingredient = await self._ingredient_repository.get_by_id(
                item.ingredient_id
            )
            if ingredient is None:
                raise IngredientNotFoundError(item.ingredient_id)

            inventory_item = InventoryItem.create(
                id=str(uuid.uuid4()),
                user_id=dto.user_id,
                ingredient=ingredient,
                quantity_state=QuantityState.IN,
                storage_location=ingredient.default_storage_location,
                added_at=now,
                today=today,
                purchase_date=purchase_date,
            )
            await self._inventory_item_repository.add(inventory_item)
            await self._shopping_list_item_repository.remove(item.id)
            added.append(InventoryItemMapper.to_output(inventory_item, ingredient))

        return added
