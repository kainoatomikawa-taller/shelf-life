"""RecipeRepository interface.

Describes the persistence operations the domain needs for the recipe
catalog. Implementations live in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.recipe import Recipe


class RecipeRepository(ABC):
    """Abstraction over recipe catalog persistence."""

    @abstractmethod
    async def add(self, recipe: Recipe) -> None:
        """Persist a new recipe to the catalog."""

    @abstractmethod
    async def get_by_id(self, recipe_id: str) -> Recipe | None:
        """Return the recipe with the given id, or None."""

    @abstractmethod
    async def list_all(self) -> list[Recipe]:
        """Return every recipe in the catalog.

        The candidate pool for the Cook Now feed (§10 Steps 1-4): the feed
        use case hard-filters and ranks this full list rather than a
        pre-narrowed one, so ranking stays in the domain/application layers.
        """

    @abstractmethod
    async def list_by_ingredient(self, ingredient_id: str) -> list[Recipe]:
        """Return all recipes that call for the given ingredient."""

    @abstractmethod
    async def update(self, recipe: Recipe) -> None:
        """Persist changes to an existing recipe."""

    @abstractmethod
    async def delete(self, recipe_id: str) -> None:
        """Remove a recipe from the catalog by id."""
