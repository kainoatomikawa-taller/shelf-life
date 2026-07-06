"""PostgreSQL implementation of the InventoryItemRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns. Freshness fields are already resolved
by the domain layer before an item reaches this repository, so they are
persisted and read back verbatim rather than recomputed.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.inventory_item import InventoryItem
from src.domain.repositories.inventory_item_repository import InventoryItemRepository
from src.domain.value_objects.freshness_date_type import FreshnessDateType
from src.domain.value_objects.freshness_display_status import FreshnessDisplayStatus
from src.domain.value_objects.quantity_state import QuantityState
from src.domain.value_objects.storage_location import StorageLocation
from src.infrastructure.database.models import InventoryItemModel


class PostgresInventoryItemRepository(InventoryItemRepository):
    """Persists inventory items in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: InventoryItem) -> None:
        self._session.add(self._to_model(item))
        await self._session.commit()

    async def get_by_id(self, item_id: str) -> InventoryItem | None:
        result = await self._session.execute(
            select(InventoryItemModel).where(InventoryItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: str) -> list[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItemModel).where(InventoryItemModel.user_id == user_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, item: InventoryItem) -> None:
        model = await self._session.get(InventoryItemModel, item.id)
        if model is None:
            return
        self._apply_to_model(item, model)
        await self._session.commit()

    async def delete(self, item_id: str) -> None:
        await self._session.execute(
            delete(InventoryItemModel).where(InventoryItemModel.id == item_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @classmethod
    def _to_model(cls, item: InventoryItem) -> InventoryItemModel:
        model = InventoryItemModel(id=item.id, user_id=item.user_id)
        cls._apply_to_model(item, model)
        return model

    @staticmethod
    def _apply_to_model(item: InventoryItem, model: InventoryItemModel) -> None:
        model.ingredient_id = item.ingredient_id
        model.quantity_state = item.quantity_state.value
        model.storage_location = item.storage_location.value
        model.purchase_date = item.purchase_date
        model.printed_package_date = item.printed_package_date
        model.is_frozen = item.is_frozen
        model.computed_freshness_date = item.computed_freshness_date
        model.freshness_date_type = item.freshness_date_type.value
        model.freshness_status = item.freshness_status.value
        model.added_at = item.added_at
        model.notes = item.notes

    @staticmethod
    def _to_entity(model: InventoryItemModel) -> InventoryItem:
        return InventoryItem(
            id=model.id,
            user_id=model.user_id,
            ingredient_id=model.ingredient_id,
            quantity_state=QuantityState(model.quantity_state),
            storage_location=StorageLocation(model.storage_location),
            computed_freshness_date=model.computed_freshness_date,
            freshness_date_type=FreshnessDateType(model.freshness_date_type),
            freshness_status=FreshnessDisplayStatus(model.freshness_status),
            added_at=model.added_at,
            purchase_date=model.purchase_date,
            printed_package_date=model.printed_package_date,
            is_frozen=model.is_frozen,
            notes=model.notes,
        )
