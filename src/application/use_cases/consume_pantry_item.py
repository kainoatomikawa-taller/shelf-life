"""ConsumePantryItem use case.

Reduces the stored quantity of a pantry item. If the item is fully consumed it
is removed from the pantry.
"""

from __future__ import annotations

from datetime import date

from src.application.dtos.pantry_item_dtos import (
    ConsumePantryItemInput,
    PantryItemOutput,
)
from src.application.mappers.pantry_item_mapper import PantryItemMapper
from src.domain.exceptions import PantryItemNotFoundError
from src.domain.repositories.pantry_item_repository import PantryItemRepository
from src.domain.value_objects.quantity import Quantity, Unit


class ConsumePantryItemUseCase:
    """Consume some quantity of an existing pantry item."""

    def __init__(self, repository: PantryItemRepository) -> None:
        self._repository = repository

    async def execute(
        self, dto: ConsumePantryItemInput
    ) -> PantryItemOutput | None:
        item = await self._repository.get_by_id(dto.item_id)
        if item is None:
            raise PantryItemNotFoundError(dto.item_id)

        amount = Quantity(amount=dto.amount, unit=Unit(dto.unit))
        item.consume(amount)

        if item.quantity.is_empty:
            await self._repository.delete(item.id)
            return None

        await self._repository.update(item)
        return PantryItemMapper.to_output(item, today=date.today())
