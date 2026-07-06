"""ListPantryItems use case.

Returns all pantry items for an owner, ordered with the most urgent
(expired / expiring soon) first. Uses the ExpirationService domain service to
apply the ordering rule.
"""

from __future__ import annotations

from datetime import date

from src.application.dtos.pantry_item_dtos import (
    ListPantryItemsInput,
    PantryItemOutput,
)
from src.application.mappers.pantry_item_mapper import PantryItemMapper
from src.domain.repositories.pantry_item_repository import PantryItemRepository
from src.domain.services.expiration_service import ExpirationService


class ListPantryItemsUseCase:
    """List all pantry items belonging to an owner."""

    def __init__(
        self,
        repository: PantryItemRepository,
        expiration_service: ExpirationService,
    ) -> None:
        self._repository = repository
        self._expiration_service = expiration_service

    async def execute(
        self, dto: ListPantryItemsInput
    ) -> list[PantryItemOutput]:
        today = date.today()
        items = await self._repository.list_by_owner(dto.owner_id)

        urgent = self._expiration_service.items_needing_attention(items, today)
        urgent_ids = {item.id for item in urgent}
        rest = [item for item in items if item.id not in urgent_ids]

        ordered = urgent + rest
        return [PantryItemMapper.to_output(item, today) for item in ordered]
