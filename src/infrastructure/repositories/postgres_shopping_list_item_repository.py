"""PostgreSQL implementation of the ShoppingListItemRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.shopping_list_item import ShoppingListItem
from src.domain.repositories.shopping_list_item_repository import (
    ShoppingListItemRepository,
)
from src.infrastructure.database.models import ShoppingListItemModel


class PostgresShoppingListItemRepository(ShoppingListItemRepository):
    """Persists shopping list items in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: ShoppingListItem) -> None:
        self._session.add(self._to_model(item))
        await self._session.commit()

    async def list_by_user(self, user_id: str) -> list[ShoppingListItem]:
        result = await self._session.execute(
            select(ShoppingListItemModel).where(
                ShoppingListItemModel.user_id == user_id
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    # --- Mapping helpers ----------------------------------------------------

    @staticmethod
    def _to_model(item: ShoppingListItem) -> ShoppingListItemModel:
        return ShoppingListItemModel(
            id=item.id,
            user_id=item.user_id,
            ingredient_id=item.ingredient_id,
            recipe_id=item.recipe_id,
            added_at=item.added_at,
        )

    @staticmethod
    def _to_entity(model: ShoppingListItemModel) -> ShoppingListItem:
        return ShoppingListItem(
            id=model.id,
            user_id=model.user_id,
            ingredient_id=model.ingredient_id,
            recipe_id=model.recipe_id,
            added_at=model.added_at,
        )
