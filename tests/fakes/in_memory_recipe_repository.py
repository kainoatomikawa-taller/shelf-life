"""In-memory RecipeRepository for fast, isolated use case tests."""

from __future__ import annotations

from src.domain.entities.recipe import Recipe
from src.domain.repositories.recipe_repository import RecipeRepository


class InMemoryRecipeRepository(RecipeRepository):
    def __init__(self, recipes: list[Recipe] | None = None) -> None:
        self._recipes: dict[str, Recipe] = {r.id: r for r in (recipes or [])}

    async def add(self, recipe: Recipe) -> None:
        self._recipes[recipe.id] = recipe

    async def get_by_id(self, recipe_id: str) -> Recipe | None:
        return self._recipes.get(recipe_id)

    async def list_all(self) -> list[Recipe]:
        return list(self._recipes.values())

    async def list_by_ingredient(self, ingredient_id: str) -> list[Recipe]:
        return [
            recipe
            for recipe in self._recipes.values()
            if any(i.ingredient_id == ingredient_id for i in recipe.ingredients)
        ]

    async def update(self, recipe: Recipe) -> None:
        self._recipes[recipe.id] = recipe

    async def delete(self, recipe_id: str) -> None:
        self._recipes.pop(recipe_id, None)
