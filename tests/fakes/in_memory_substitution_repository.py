"""In-memory SubstitutionRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.substitution import Substitution
from src.domain.repositories.substitution_repository import SubstitutionRepository
from src.domain.value_objects.substitution_context import SubstitutionContext


class InMemorySubstitutionRepository(SubstitutionRepository):
    def __init__(self, substitutions: list[Substitution] | None = None) -> None:
        self._substitutions: dict[str, Substitution] = {
            s.id: s for s in (substitutions or [])
        }

    async def add(self, substitution: Substitution) -> None:
        self._substitutions[substitution.id] = substitution

    async def get_by_id(self, substitution_id: str) -> Substitution | None:
        return self._substitutions.get(substitution_id)

    async def find_for_ingredient(self, from_ingredient_id: str) -> list[Substitution]:
        return [
            s
            for s in self._substitutions.values()
            if s.from_ingredient_id == from_ingredient_id
        ]

    async def find_by_context(
        self, context: SubstitutionContext
    ) -> list[Substitution]:
        return [s for s in self._substitutions.values() if s.context is context]

    async def update(self, substitution: Substitution) -> None:
        self._substitutions[substitution.id] = substitution

    async def delete(self, substitution_id: str) -> None:
        self._substitutions.pop(substitution_id, None)
