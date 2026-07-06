"""PantryItemRepository interface.

Describes the persistence operations the domain needs, without committing to
any particular database or ORM. Implementations live in the infrastructure
layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.pantry_item import PantryItem


class PantryItemRepository(ABC):
    """Abstraction over pantry item persistence."""

    @abstractmethod
    async def add(self, item: PantryItem) -> None:
        """Persist a new pantry item."""

    @abstractmethod
    async def get_by_id(self, item_id: str) -> PantryItem | None:
        """Return the item with the given id, or None if it does not exist."""

    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list[PantryItem]:
        """Return all pantry items belonging to the given owner."""

    @abstractmethod
    async def update(self, item: PantryItem) -> None:
        """Persist changes to an existing pantry item."""

    @abstractmethod
    async def delete(self, item_id: str) -> None:
        """Remove a pantry item by id."""
