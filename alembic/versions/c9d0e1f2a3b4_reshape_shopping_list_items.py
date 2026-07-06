"""Reshape shopping_list_items: recipe_id -> source_recipe_ids, add checked
and quantity_needed (§8 schema).

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-07-06

Design notes
------------
* source_recipe_ids replaces the single recipe_id FK — the same ingredient
  can now be tracked as needed by more than one recipe on a user's list.
  Existing rows are backfilled with their prior recipe_id as the sole
  element.
* checked defaults to false. quantity_needed is optional and flattened
  into amount/unit columns, following the Quantity value object's
  convention used for pantry items.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "c9d0e1f2a3b4"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shopping_list_items",
        sa.Column(
            "source_recipe_ids",
            ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )
    op.execute(
        "UPDATE shopping_list_items SET source_recipe_ids = ARRAY[recipe_id]"
    )
    op.drop_constraint(
        "shopping_list_items_recipe_id_fkey",
        "shopping_list_items",
        type_="foreignkey",
    )
    op.drop_column("shopping_list_items", "recipe_id")

    op.add_column(
        "shopping_list_items",
        sa.Column("checked", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "shopping_list_items",
        sa.Column("quantity_needed_amount", sa.Float, nullable=True),
    )
    op.add_column(
        "shopping_list_items",
        sa.Column("quantity_needed_unit", sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shopping_list_items", "quantity_needed_unit")
    op.drop_column("shopping_list_items", "quantity_needed_amount")
    op.drop_column("shopping_list_items", "checked")

    op.add_column(
        "shopping_list_items",
        sa.Column("recipe_id", sa.String(36), nullable=True),
    )
    op.execute("UPDATE shopping_list_items SET recipe_id = source_recipe_ids[1]")
    op.alter_column("shopping_list_items", "recipe_id", nullable=False)
    op.create_foreign_key(
        "shopping_list_items_recipe_id_fkey",
        "shopping_list_items",
        "recipes",
        ["recipe_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("shopping_list_items", "source_recipe_ids")
