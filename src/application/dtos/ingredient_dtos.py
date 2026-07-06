"""Data transfer objects for the ingredient catalog search use case.

These are plain data contracts that cross the boundary between the interfaces
layer and the application layer. They never expose domain entities directly.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchIngredientsInput:
    query: str
    limit: int = 20


@dataclass(frozen=True)
class IngredientSummaryOutput:
    id: str
    name: str
    aliases: tuple[str, ...]
    category: str
    default_storage_location: str
