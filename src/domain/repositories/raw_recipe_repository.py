"""RawRecipeRepository interface.

Describes the persistence operations the domain needs for the raw-recipe
staging area. Deliberately separate from RecipeRepository — implementations
back onto a different table, so staged, unreviewed data can never leak into
the production Recipe catalog through a shared persistence path.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.raw_recipe import RawRecipe
from src.domain.value_objects.pipeline_stage import PipelineStage


class RawRecipeRepository(ABC):
    """Abstraction over raw-recipe staging persistence."""

    @abstractmethod
    async def add(self, raw_recipe: RawRecipe) -> None:
        """Persist a newly imported raw recipe."""

    @abstractmethod
    async def get_by_id(self, raw_recipe_id: str) -> RawRecipe | None:
        """Return the raw recipe with the given id, or None."""

    @abstractmethod
    async def get_by_source(
        self, source: str, source_recipe_id: str
    ) -> RawRecipe | None:
        """Return the raw recipe previously imported from this source and
        source recipe id, or None. Used to detect duplicate imports."""

    @abstractmethod
    async def list_by_stage(self, stage: PipelineStage) -> list[RawRecipe]:
        """Return every raw recipe currently sitting at the given pipeline
        stage — the work queue for that stage's operator."""

    @abstractmethod
    async def update(self, raw_recipe: RawRecipe) -> None:
        """Persist changes to an existing raw recipe."""

    @abstractmethod
    async def delete(self, raw_recipe_id: str) -> None:
        """Remove a raw recipe from staging by id."""
