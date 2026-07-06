"""PostgreSQL implementation of the RatingRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.rating import Rating
from src.domain.repositories.rating_repository import RatingRepository
from src.infrastructure.database.models import RatingModel


class PostgresRatingRepository(RatingRepository):
    """Persists ratings in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, rating: Rating) -> None:
        self._session.add(self._to_model(rating))
        await self._session.commit()

    async def list_by_user(self, user_id: str) -> list[Rating]:
        result = await self._session.execute(
            select(RatingModel).where(RatingModel.user_id == user_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    # --- Mapping helpers ----------------------------------------------------

    @staticmethod
    def _to_model(rating: Rating) -> RatingModel:
        return RatingModel(
            id=rating.id,
            user_id=rating.user_id,
            recipe_id=rating.recipe_id,
            stars=rating.stars,
            quick_tags=rating.quick_tags,
            made_it_at=rating.made_it_at,
        )

    @staticmethod
    def _to_entity(model: RatingModel) -> Rating:
        return Rating(
            id=model.id,
            user_id=model.user_id,
            recipe_id=model.recipe_id,
            stars=model.stars,
            made_it_at=model.made_it_at,
            quick_tags=list(model.quick_tags),
        )
