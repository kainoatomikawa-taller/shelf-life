"""PostgreSQL implementation of the PantryItemRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it only
translates persistence concerns.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.pantry_item import PantryItem
from src.domain.repositories.pantry_item_repository import PantryItemRepository
from src.domain.value_objects.quantity import Quantity, Unit
from src.infrastructure.database.models import PantryItemModel


class PostgresPantryItemRepository(PantryItemRepository):
    """Persists pantry items in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: PantryItem) -> None:
        self._session.add(self._to_model(item))
        await self._session.commit()

    async def get_by_id(self, item_id: str) -> PantryItem | None:
        result = await self._session.execute(
            select(PantryItemModel).where(PantryItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_owner(self, owner_id: str) -> list[PantryItem]:
        result = await self._session.execute(
            select(PantryItemModel).where(PantryItemModel.owner_id == owner_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, item: PantryItem) -> None:
        model = await self._session.get(PantryItemModel, item.id)
        if model is None:
            return
        model.name = item.name
        model.amount = item.quantity.amount
        model.unit = item.quantity.unit.value
        model.expiration_date = item.expiration_date
        await self._session.commit()

    async def delete(self, item_id: str) -> None:
        await self._session.execute(
            delete(PantryItemModel).where(PantryItemModel.id == item_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @staticmethod
    def _to_model(item: PantryItem) -> PantryItemModel:
        return PantryItemModel(
            id=item.id,
            owner_id=item.owner_id,
            name=item.name,
            amount=item.quantity.amount,
            unit=item.quantity.unit.value,
            expiration_date=item.expiration_date,
        )

    @staticmethod
    def _to_entity(model: PantryItemModel) -> PantryItem:
        return PantryItem(
            id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            quantity=Quantity(amount=model.amount, unit=Unit(model.unit)),
            expiration_date=model.expiration_date,
        )
