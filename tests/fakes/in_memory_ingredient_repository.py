"""In-memory IngredientRepository for fast, isolated use case tests.

Demonstrates that use cases depend only on the domain interface, not on any
concrete database.
"""

from __future__ import annotations

from src.domain.entities.ingredient import Ingredient
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.value_objects.ingredient_category import IngredientCategory


class InMemoryIngredientRepository(IngredientRepository):
    def __init__(self) -> None:
        self._ingredients: dict[str, Ingredient] = {}

    async def add(self, ingredient: Ingredient) -> None:
        self._ingredients[ingredient.id] = ingredient

    async def get_by_id(self, ingredient_id: str) -> Ingredient | None:
        return self._ingredients.get(ingredient_id)

    async def find_by_name_or_alias(self, query: str) -> list[Ingredient]:
        return [i for i in self._ingredients.values() if i.matches_query(query)]

    async def search(self, query: str, limit: int = 20) -> list[Ingredient]:
        ranked = sorted(
            (
                (rank, ingredient)
                for ingredient in self._ingredients.values()
                if (rank := ingredient.search_rank(query)) is not None
            ),
            key=lambda pair: (pair[0], pair[1].name),
        )
        return [ingredient for _, ingredient in ranked[:limit]]

    async def list_by_category(self, category: IngredientCategory) -> list[Ingredient]:
        return [i for i in self._ingredients.values() if i.category == category]

    async def update(self, ingredient: Ingredient) -> None:
        self._ingredients[ingredient.id] = ingredient

    async def delete(self, ingredient_id: str) -> None:
        self._ingredients.pop(ingredient_id, None)
