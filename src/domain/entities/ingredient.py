"""Ingredient entity.

A catalog entry describing a type of food ingredient — its storage
characteristics, shelf life per storage location, and dietary metadata.
It has no knowledge of persistence, transport, or frameworks.
"""

from __future__ import annotations

from src.domain.exceptions import ValidationError
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.storage_location import StorageLocation


class Ingredient:
    """A catalog entry for a type of ingredient."""

    def __init__(
        self,
        id: str,
        name: str,
        aliases: list[str],
        category: IngredientCategory,
        default_storage_location: StorageLocation,
        typical_shelf_life: ShelfLifeByStorage,
        allergen_tags: list[str],
        diet_tags: list[str],
    ) -> None:
        if not id:
            raise ValidationError("Ingredient id is required.")
        if not name or not name.strip():
            raise ValidationError("Ingredient name cannot be empty.")

        self._id = id
        self._name = name.strip()
        self._aliases = list(aliases)
        self._category = category
        self._default_storage_location = default_storage_location
        self._typical_shelf_life = typical_shelf_life
        self._allergen_tags = list(allergen_tags)
        self._diet_tags = list(diet_tags)

    # --- Identity & read-only accessors ----------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def aliases(self) -> list[str]:
        return list(self._aliases)

    @property
    def category(self) -> IngredientCategory:
        return self._category

    @property
    def default_storage_location(self) -> StorageLocation:
        return self._default_storage_location

    @property
    def typical_shelf_life(self) -> ShelfLifeByStorage:
        return self._typical_shelf_life

    @property
    def allergen_tags(self) -> list[str]:
        return list(self._allergen_tags)

    @property
    def diet_tags(self) -> list[str]:
        return list(self._diet_tags)

    # --- Behaviour -------------------------------------------------------------

    def matches_query(self, query: str) -> bool:
        """True if query matches the canonical name or any alias (case-insensitive)."""
        q = query.lower().strip()
        return q == self._name.lower() or q in {a.lower() for a in self._aliases}

    def add_alias(self, alias: str) -> None:
        """Register an additional alias, ignoring case-duplicate entries."""
        if not alias or not alias.strip():
            raise ValidationError("Alias cannot be empty.")
        normalized = alias.strip()
        if normalized.lower() not in {a.lower() for a in self._aliases}:
            self._aliases.append(normalized)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ingredient):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
