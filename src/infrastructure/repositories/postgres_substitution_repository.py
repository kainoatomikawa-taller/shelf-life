"""PostgreSQL implementation of the SubstitutionRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns. NUMERIC confidence values come back
as Decimal from the driver and are cast to float for the domain entity.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.substitution import Substitution
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.value_objects.substitution_context import SubstitutionContext
from src.infrastructure.database.models import SubstitutionModel


class PostgresSubstitutionRepository(SubstitutionRepository):
    """Persists substitutions in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, substitution: Substitution) -> None:
        self._session.add(self._to_model(substitution))
        await self._session.commit()

    async def get_by_id(self, substitution_id: str) -> Substitution | None:
        model = await self._session.get(SubstitutionModel, substitution_id)
        return self._to_entity(model) if model else None

    async def find_for_ingredient(self, from_ingredient_id: str) -> list[Substitution]:
        result = await self._session.execute(
            select(SubstitutionModel).where(
                SubstitutionModel.from_ingredient_id == from_ingredient_id
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def find_by_context(
        self, context: SubstitutionContext
    ) -> list[Substitution]:
        result = await self._session.execute(
            select(SubstitutionModel).where(
                SubstitutionModel.context == context.value
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, substitution: Substitution) -> None:
        model = await self._session.get(SubstitutionModel, substitution.id)
        if model is None:
            return
        self._apply_to_model(substitution, model)
        await self._session.commit()

    async def delete(self, substitution_id: str) -> None:
        await self._session.execute(
            delete(SubstitutionModel).where(SubstitutionModel.id == substitution_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @classmethod
    def _to_model(cls, substitution: Substitution) -> SubstitutionModel:
        model = SubstitutionModel(id=substitution.id)
        cls._apply_to_model(substitution, model)
        return model

    @staticmethod
    def _apply_to_model(substitution: Substitution, model: SubstitutionModel) -> None:
        model.from_ingredient_id = substitution.from_ingredient_id
        model.to_ingredient_id = substitution.to_ingredient_id
        model.context = substitution.context.value
        model.ratio_note = substitution.ratio_note
        model.impact_note = substitution.impact_note
        model.confidence = substitution.confidence

    @staticmethod
    def _to_entity(model: SubstitutionModel) -> Substitution:
        return Substitution(
            id=model.id,
            from_ingredient_id=model.from_ingredient_id,
            to_ingredient_id=model.to_ingredient_id,
            context=SubstitutionContext(model.context),
            confidence=float(model.confidence),
            ratio_note=model.ratio_note,
            impact_note=model.impact_note,
        )
