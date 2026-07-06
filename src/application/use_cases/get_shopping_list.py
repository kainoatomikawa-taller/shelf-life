"""GetShoppingList use case (§5.7 AC1).

Backs the Shopping List tab: aggregates every ingredient the user has
committed to buy — via Discover's one-tap add and via ingredients newly
flagged Low/Out in their Kitchen inventory — merging duplicates so the same
ingredient never appears twice regardless of source. Low/out-flagged
ingredients not yet on the list are persisted as new ShoppingListItems (with
no recipe provenance, via ShoppingListAggregator) so their checked state can
be tracked and survives across requests, exactly like Discover-sourced items.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.application.dtos.shopping_list_dtos import (
    GetShoppingListInput,
    ShoppingListEntryOutput,
)
from src.application.mappers.shopping_list_item_mapper import ShoppingListItemMapper
from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.exceptions import IngredientNotFoundError, UserNotFoundError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.shopping_list_aggregator import ShoppingListAggregator
from src.domain.value_objects.quantity_state import QuantityState

_LOW_STOCK_STATES = (QuantityState.LOW, QuantityState.OUT)


class GetShoppingListUseCase:
    """Return the user's merged Shopping List tab contents."""

    def __init__(
        self,
        shopping_list_item_repository: ShoppingListItemRepository,
        inventory_item_repository: InventoryItemRepository,
        ingredient_repository: IngredientRepository,
        user_repository: UserRepository,
        aggregator: ShoppingListAggregator | None = None,
    ) -> None:
        self._shopping_list_item_repository = shopping_list_item_repository
        self._inventory_item_repository = inventory_item_repository
        self._ingredient_repository = ingredient_repository
        self._user_repository = user_repository
        self._aggregator = aggregator or ShoppingListAggregator()

    async def execute(
        self, dto: GetShoppingListInput
    ) -> list[ShoppingListEntryOutput]:
        user = await self._user_repository.get_by_id(dto.user_id)
        if user is None:
            raise UserNotFoundError(dto.user_id)

        existing_items = await self._shopping_list_item_repository.list_by_user(
            dto.user_id
        )

        inventory_items = await self._inventory_item_repository.list_by_user(
            dto.user_id
        )
        low_stock_ingredient_ids = [
            item.ingredient_id
            for item in inventory_items
            if item.quantity_state in _LOW_STOCK_STATES
        ]

        missing_ingredient_ids = self._aggregator.missing_low_stock_entries(
            existing_items, low_stock_ingredient_ids
        )

        now = datetime.now(UTC)
        new_items: list[ShoppingListItem] = []
        for ingredient_id in missing_ingredient_ids:
            item = ShoppingListItem(
                id=str(uuid.uuid4()),
                user_id=dto.user_id,
                ingredient_id=ingredient_id,
                source_recipe_ids=[],
                added_at=now,
            )
            await self._shopping_list_item_repository.add(item)
            new_items.append(item)

        outputs: list[ShoppingListEntryOutput] = []
        for item in [*existing_items, *new_items]:
            ingredient = await self._ingredient_repository.get_by_id(
                item.ingredient_id
            )
            if ingredient is None:
                raise IngredientNotFoundError(item.ingredient_id)
            outputs.append(ShoppingListItemMapper.to_output(item, ingredient))
        return outputs
