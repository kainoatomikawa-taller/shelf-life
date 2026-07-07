"""Create ingredients table (§8 catalog schema).

Revision ID: e3a1f2c4d5b6
Revises: None
Create Date: 2026-07-06

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e3a1f2c4d5b6"
down_revision = None
branch_labels = None
depends_on = None

# Five storage-based categories an ingredient can belong to.
_INGREDIENT_CATEGORY = postgresql.ENUM(
    "perishable_fridge",
    "perishable_counter",
    "frozen",
    "pantry",
    "spice",
    name="ingredient_category",
)

# Four physical locations where an ingredient can be stored.
_STORAGE_LOCATION = postgresql.ENUM(
    "fridge",
    "counter",
    "freezer",
    "pantry",
    name="storage_location",
)


def upgrade() -> None:
    _INGREDIENT_CATEGORY.create(op.get_bind(), checkfirst=True)
    _STORAGE_LOCATION.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ingredients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        # aliases: searchable array — see GIN index below (AC-4).
        sa.Column(
            "aliases",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "perishable_fridge",
                "perishable_counter",
                "frozen",
                "pantry",
                "spice",
                name="ingredient_category",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "default_storage_location",
            postgresql.ENUM(
                "fridge",
                "counter",
                "freezer",
                "pantry",
                name="storage_location",
                create_type=False,
            ),
            nullable=False,
        ),
        # typicalShelfLifeByStorage — per-location typical shelf life in days.
        sa.Column("shelf_life_fridge_days", sa.Integer(), nullable=True),
        sa.Column("shelf_life_counter_days", sa.Integer(), nullable=True),
        sa.Column("shelf_life_freezer_days", sa.Integer(), nullable=True),
        sa.Column("shelf_life_pantry_days", sa.Integer(), nullable=True),
        sa.Column(
            "allergen_tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "diet_tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )

    op.create_index("ix_ingredients_name", "ingredients", ["name"])

    # GIN index on aliases allows efficient `'scallion' = ANY(aliases)` queries
    # so that searching for an alias surfaces the canonical ingredient (AC-4).
    op.create_index(
        "ix_ingredients_aliases_gin",
        "ingredients",
        ["aliases"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_ingredients_aliases_gin", table_name="ingredients")
    op.drop_index("ix_ingredients_name", table_name="ingredients")
    op.drop_table("ingredients")

    _INGREDIENT_CATEGORY.drop(op.get_bind(), checkfirst=True)
    _STORAGE_LOCATION.drop(op.get_bind(), checkfirst=True)
