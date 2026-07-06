"""Create shopping_list_items table (§8 schema).

Revision ID: a4b5c6d7e8f9
Revises: e7f8a9b0c1d2
Create Date: 2026-07-06

Design notes
------------
* One row per ingredient a user committed to buy via the Discover
  screen's one-tap "add" (§5.4) — populated exclusively by
  AddShoppingListItemsUseCase, never edited in place.
* recipe_id is provenance only (which recipe's shopping list produced the
  row); it doesn't gate reads.
* FKs to users, ingredients, and recipes use ON DELETE CASCADE so removing
  any parent record cleans up dependent shopping list rows.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a4b5c6d7e8f9"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recipe_id",
            sa.String(36),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index(
        "ix_shopping_list_items_user_id", "shopping_list_items", ["user_id"]
    )
    op.create_index(
        "ix_shopping_list_items_ingredient_id",
        "shopping_list_items",
        ["ingredient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_shopping_list_items_ingredient_id", table_name="shopping_list_items"
    )
    op.drop_index("ix_shopping_list_items_user_id", table_name="shopping_list_items")
    op.drop_table("shopping_list_items")
