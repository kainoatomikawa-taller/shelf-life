"""SQLAlchemy ORM models.

ORM types are confined to the infrastructure layer and never leak into
domain or application.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, Float, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.engine import Base

# Named enum types — defined once so SQLAlchemy does not attempt duplicate DDL.
_ingredient_category = Enum(
    "perishable_fridge",
    "perishable_counter",
    "frozen",
    "pantry",
    "spice",
    name="ingredient_category",
)

_storage_location = Enum(
    "fridge",
    "counter",
    "freezer",
    "pantry",
    name="storage_location",
)


class PantryItemModel(Base):
    """Persistence representation of a pantry item."""

    __tablename__ = "pantry_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)


class IngredientModel(Base):
    """Persistence representation of a catalog ingredient (§8 schema)."""

    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Queryable via GIN index; use `'alias' = ANY(aliases)` in queries.
    aliases: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    category: Mapped[str] = mapped_column(_ingredient_category, nullable=False)
    default_storage_location: Mapped[str] = mapped_column(
        _storage_location, nullable=False
    )

    # typicalShelfLifeByStorage — per-location values in days, None = not applicable.
    shelf_life_fridge_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_counter_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_freezer_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shelf_life_pantry_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    allergen_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )
    diet_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
    )

    __table_args__ = (
        # GIN index enables efficient `'alias' = ANY(aliases)` lookups (AC-4).
        Index("ix_ingredients_aliases_gin", "aliases", postgresql_using="gin"),
    )
