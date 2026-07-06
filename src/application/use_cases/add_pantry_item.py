"""AddPantryItem use case.

Creates a new pantry item for an owner and persists it via the repository
interface. Receives its dependencies through the constructor (DI).
"""

from __future__ import annotations

import uuid
from datetime import date

from src.application.dtos.pantry_item_dtos import (
    AddPantryItemInput,
    PantryItemOutput,
)
from src.application.mappers.pantry_item_mapper import PantryItemMapper
from src.domain.entities.pantry_item import PantryItem
from src.domain.repositories.pantry_item_repository import PantryItemRepository
from src.domain.value_objects.quantity import Quantity, Unit


class AddPantryItemUseCase:
    """Add a new item to a user's pantry."""

    def __init__(self, repository: PantryItemRepository) -> None:
        self._repository = repository

    async def execute(self, dto: AddPantryItemInput) -> PantryItemOutput:
        quantity = Quantity(amount=dto.amount, unit=Unit(dto.unit))
        item = PantryItem(
            id=str(uuid.uuid4()),
            owner_id=dto.owner_id,
            name=dto.name,
            quantity=quantity,
            expiration_date=dto.expiration_date,
        )
        await self._repository.add(item)
        return PantryItemMapper.to_output(item, today=date.today())
