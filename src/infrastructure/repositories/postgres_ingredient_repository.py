"""PostgreSQL implementation of the IngredientRepository interface.

Maps between ORM rows and domain entities. Contains no business logic — it
only translates persistence concerns. Relevance ranking for `search` is
delegated to Ingredient.search_rank so the matching rules live in the
domain layer, not here.
"""

from __future__ import annotations

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ingredient import Ingredient
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.shelf_life_by_storage import ShelfLifeByStorage
from src.domain.value_objects.shelf_life_model import ShelfLifeModel
from src.domain.value_objects.storage_location import StorageLocation
from src.infrastructure.database.models import IngredientModel


class PostgresIngredientRepository(IngredientRepository):
    """Persists catalog ingredients in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, ingredient: Ingredient) -> None:
        self._session.add(self._to_model(ingredient))
        await self._session.commit()

    async def get_by_id(self, ingredient_id: str) -> Ingredient | None:
        result = await self._session.execute(
            select(IngredientModel).where(IngredientModel.id == ingredient_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_name_or_alias(self, query: str) -> list[Ingredient]:
        q = query.lower().strip()
        # array_to_string(...).ilike(q) coarsely narrows candidates using the
        # GIN-backed aliases column; matches_query() then applies the exact,
        # case-insensitive comparison the domain contract requires.
        result = await self._session.execute(
            select(IngredientModel).where(
                or_(
                    func.lower(IngredientModel.name) == q,
                    func.lower(
                        func.array_to_string(IngredientModel.aliases, ",")
                    ).ilike(f"%{q}%"),
                )
            )
        )
        return [
            ingredient
            for model in result.scalars().all()
            if (ingredient := self._to_entity(model)).matches_query(query)
        ]

    async def search(self, query: str, limit: int = 20) -> list[Ingredient]:
        q = query.lower().strip()
        if not q:
            return []
        pattern = f"%{q}%"
        result = await self._session.execute(
            select(IngredientModel).where(
                or_(
                    func.lower(IngredientModel.name).ilike(pattern),
                    func.lower(
                        func.array_to_string(IngredientModel.aliases, ",")
                    ).ilike(pattern),
                )
            )
        )
        candidates = [self._to_entity(model) for model in result.scalars().all()]
        ranked = sorted(
            (
                (rank, ingredient)
                for ingredient in candidates
                if (rank := ingredient.search_rank(query)) is not None
            ),
            key=lambda pair: (pair[0], pair[1].name),
        )
        return [ingredient for _, ingredient in ranked[:limit]]

    async def list_by_category(self, category: IngredientCategory) -> list[Ingredient]:
        result = await self._session.execute(
            select(IngredientModel).where(
                IngredientModel.category == category.value
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def update(self, ingredient: Ingredient) -> None:
        model = await self._session.get(IngredientModel, ingredient.id)
        if model is None:
            return
        self._apply_to_model(ingredient, model)
        await self._session.commit()

    async def delete(self, ingredient_id: str) -> None:
        await self._session.execute(
            delete(IngredientModel).where(IngredientModel.id == ingredient_id)
        )
        await self._session.commit()

    # --- Mapping helpers ----------------------------------------------------

    @classmethod
    def _to_model(cls, ingredient: Ingredient) -> IngredientModel:
        model = IngredientModel(id=ingredient.id)
        cls._apply_to_model(ingredient, model)
        return model

    @staticmethod
    def _apply_to_model(ingredient: Ingredient, model: IngredientModel) -> None:
        shelf_life = ingredient.typical_shelf_life
        model.name = ingredient.name
        model.aliases = list(ingredient.aliases)
        model.category = ingredient.category.value
        model.default_storage_location = ingredient.default_storage_location.value
        model.shelf_life_fridge_days = shelf_life.fridge_days
        model.shelf_life_counter_days = shelf_life.counter_days
        model.shelf_life_freezer_days = shelf_life.freezer_days
        model.shelf_life_pantry_days = shelf_life.pantry_days
        model.allergen_tags = list(ingredient.allergen_tags)
        model.diet_tags = list(ingredient.diet_tags)
        model.shelf_life_model = ingredient.shelf_life_model.value

    @staticmethod
    def _to_entity(model: IngredientModel) -> Ingredient:
        return Ingredient(
            id=model.id,
            name=model.name,
            aliases=list(model.aliases),
            category=IngredientCategory(model.category),
            default_storage_location=StorageLocation(model.default_storage_location),
            typical_shelf_life=ShelfLifeByStorage(
                fridge_days=model.shelf_life_fridge_days,
                counter_days=model.shelf_life_counter_days,
                freezer_days=model.shelf_life_freezer_days,
                pantry_days=model.shelf_life_pantry_days,
            ),
            allergen_tags=list(model.allergen_tags),
            diet_tags=list(model.diet_tags),
            shelf_life_model=ShelfLifeModel(model.shelf_life_model),
        )
