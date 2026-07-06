"""PostgreSQL implementation of the ShoppingListItemRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)
from src.domain.value_objects.quantity import Quantity, Unit
from src.infrastructure.database.models import ShoppingListItemModel


class PostgresShoppingListItemRepository(ShoppingListItemRepository):
    """Persists shopping list items in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: ShoppingListItem) -> None:
        self._session.add(self._to_model(item))
        await self._session.commit()

    async def get_by_id(self, item_id: str) -> ShoppingListItem | None:
        result = await self._session.execute(
            select(ShoppingListItemModel).where(ShoppingListItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(self, user_id: str) -> list[ShoppingListItem]:
        result = await self._session.execute(
            select(ShoppingListItemModel).where(
                ShoppingListItemModel.user_id == user_id
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, item: ShoppingListItem) -> None:
        model = await self._session.get(ShoppingListItemModel, item.id)
        if model is None:
            return
        self._apply_to_model(item, model)
        await self._session.commit()

    async def remove(self, item_id: str) -> None:
        await self._session.execute(
            delete(ShoppingListItemModel).where(ShoppingListItemModel.id == item_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @classmethod
    def _to_model(cls, item: ShoppingListItem) -> ShoppingListItemModel:
        model = ShoppingListItemModel(id=item.id, user_id=item.user_id)
        cls._apply_to_model(item, model)
        return model

    @staticmethod
    def _apply_to_model(item: ShoppingListItem, model: ShoppingListItemModel) -> None:
        quantity_needed = item.quantity_needed
        model.ingredient_id = item.ingredient_id
        model.source_recipe_ids = item.source_recipe_ids
        model.added_at = item.added_at
        model.checked = item.checked
        model.quantity_needed_amount = (
            quantity_needed.amount if quantity_needed else None
        )
        model.quantity_needed_unit = (
            quantity_needed.unit.value if quantity_needed else None
        )

    @staticmethod
    def _to_entity(model: ShoppingListItemModel) -> ShoppingListItem:
        quantity_needed = (
            Quantity(
                amount=model.quantity_needed_amount,
                unit=Unit(model.quantity_needed_unit),
            )
            if model.quantity_needed_amount is not None
            and model.quantity_needed_unit is not None
            else None
        )
        return ShoppingListItem(
            id=model.id,
            user_id=model.user_id,
            ingredient_id=model.ingredient_id,
            source_recipe_ids=list(model.source_recipe_ids),
            added_at=model.added_at,
            checked=model.checked,
            quantity_needed=quantity_needed,
        )
