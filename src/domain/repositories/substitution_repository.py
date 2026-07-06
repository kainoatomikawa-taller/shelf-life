"""SubstitutionRepository interface.

Describes the persistence operations the domain needs for the substitution
catalog. Implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.substitution import Substitution
from src.domain.value_objects.substitution_context import SubstitutionContext


class SubstitutionRepository(ABC):
    """Abstraction over substitution catalog persistence."""

    @abstractmethod
    async def add(self, substitution: Substitution) -> None:
        """Persist a new substitution."""

    @abstractmethod
    async def get_by_id(self, substitution_id: str) -> Substitution | None:
        """Return the substitution with the given id, or None."""

    @abstractmethod
    async def find_for_ingredient(
        self, from_ingredient_id: str
    ) -> list[Substitution]:
        """Return all substitutions where `from_ingredient_id` matches.

        Answers: "what can I use instead of ingredient X?"
        """

    @abstractmethod
    async def find_by_context(
        self, context: SubstitutionContext
    ) -> list[Substitution]:
        """Return all substitutions valid in the given cooking context."""

    @abstractmethod
    async def update(self, substitution: Substitution) -> None:
        """Persist changes to an existing substitution."""

    @abstractmethod
    async def delete(self, substitution_id: str) -> None:
        """Remove a substitution by id."""
