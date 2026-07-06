"""Create ratings table (§8 schema).

Revision ID: b7c8d9e0f1a2
Revises: a4b5c6d7e8f9
Create Date: 2026-07-06

Design notes
------------
* One row per cook — a user's stars, quick tags, and made_it_at timestamp
  for a recipe. Never edited in place once recorded.
* FKs to users and recipes use ON DELETE CASCADE so removing either parent
  record cleans up dependent ratings.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recipe_id",
            sa.String(36),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stars", sa.Integer, nullable=False),
        sa.Column(
            "quick_tags",
            ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("made_it_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )

    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_recipe_id", "ratings", ["recipe_id"])


def downgrade() -> None:
    op.drop_index("ix_ratings_recipe_id", table_name="ratings")
    op.drop_index("ix_ratings_user_id", table_name="ratings")
    op.drop_table("ratings")
