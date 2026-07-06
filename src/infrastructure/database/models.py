"""SQLAlchemy ORM models.

ORM types are confined to the infrastructure layer and never leak into
domain or application.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
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

_shelf_life_model_type = Enum(
    "spoilage",
    "potency",
    name="shelf_life_model_type",
)

_substitution_context_type = Enum(
    "baking",
    "savory",
    "general",
    name="substitution_context",
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

    # Distinguishes safety-based expiry (spoilage) from quality-loss (potency).
    # All spices use potency; everything else defaults to spoilage.
    shelf_life_model: Mapped[str] = mapped_column(
        _shelf_life_model_type,
        nullable=False,
        server_default="spoilage",
    )

    __table_args__ = (
        # GIN index enables efficient `'alias' = ANY(aliases)` lookups (AC-4).
        Index("ix_ingredients_aliases_gin", "aliases", postgresql_using="gin"),
    )


class SubstitutionModel(Base):
    """Persistence representation of an ingredient substitution (§8/§5.5 schema)."""

    __tablename__ = "substitutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Directed: "use to_ingredient instead of from_ingredient".
    from_ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_ingredient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Free-text ratio guidance, e.g. "use ¾ the amount".
    ratio_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    context: Mapped[str] = mapped_column(_substitution_context_type, nullable=False)

    # Free-text description of the culinary impact of the swap.
    impact_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # NUMERIC(4,3) stores exact decimals 0.000–1.000; supports reliable >= comparisons.
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(precision=4, scale=3), nullable=False
    )

    __table_args__ = (
        # Each ingredient pair may have at most one substitution per cooking context.
        UniqueConstraint(
            "from_ingredient_id",
            "to_ingredient_id",
            "context",
            name="uq_substitutions_pair_context",
        ),
        CheckConstraint(
            "from_ingredient_id != to_ingredient_id",
            name="ck_substitutions_no_self_reference",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_substitutions_confidence_range",
        ),
        # B-tree index supports threshold queries: WHERE confidence >= :threshold
        Index("ix_substitutions_confidence", "confidence"),
    )
