"""IngredientRepository interface.

Describes the persistence operations the domain needs for the ingredient
catalog. Implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.ingredient import Ingredient
from src.domain.value_objects.ingredient_category import IngredientCategory


class IngredientRepository(ABC):
    """Abstraction over ingredient catalog persistence."""

    @abstractmethod
    async def add(self, ingredient: Ingredient) -> None:
        """Persist a new ingredient to the catalog."""

    @abstractmethod
    async def get_by_id(self, ingredient_id: str) -> Ingredient | None:
        """Return the ingredient with the given id, or None."""

    @abstractmethod
    async def find_by_name_or_alias(self, query: str) -> list[Ingredient]:
        """Return ingredients whose name or any alias matches the query.

        Implementations should use a case-insensitive, exact-token match
        against both the canonical name and the aliases array, e.g.:
            WHERE lower(name) = lower(:q) OR lower(:q) = ANY(lower(aliases::text)::text[])
        The GIN index on aliases supports efficient array membership checks.
        """

    @abstractmethod
    async def list_by_category(self, category: IngredientCategory) -> list[Ingredient]:
        """Return all ingredients in a given category."""

    @abstractmethod
    async def update(self, ingredient: Ingredient) -> None:
        """Persist changes to an existing ingredient."""

    @abstractmethod
    async def delete(self, ingredient_id: str) -> None:
        """Remove an ingredient from the catalog by id."""
