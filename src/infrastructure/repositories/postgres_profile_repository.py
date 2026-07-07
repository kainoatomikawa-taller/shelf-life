"""PostgreSQL implementation of the ProfileRepository interface.

Maps between ORM rows and domain entities. Contains no business logic.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.profile import Profile
from src.domain.exceptions import UsernameAlreadyTakenError
from src.domain.repositories.profile_repository import ProfileRepository
from src.infrastructure.database.models import ProfileModel


class PostgresProfileRepository(ProfileRepository):
    """Persists profiles in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: Profile) -> None:
        self._session.add(
            ProfileModel(
                id=profile.id,
                username=profile.username,
                display_name=profile.display_name,
                created_at=profile.created_at,
            )
        )
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise UsernameAlreadyTakenError(profile.username) from exc

    async def get_by_id(self, profile_id: str) -> Profile | None:
        result = await self._session.execute(
            select(ProfileModel).where(ProfileModel.id == profile_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Profile | None:
        result = await self._session.execute(
            select(ProfileModel).where(ProfileModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: ProfileModel) -> Profile:
        return Profile(
            id=model.id,
            username=model.username,
            display_name=model.display_name,
            created_at=model.created_at,
        )
