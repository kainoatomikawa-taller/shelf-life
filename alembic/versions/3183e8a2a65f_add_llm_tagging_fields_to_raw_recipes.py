"""Add structured LLM-tagging fields to raw_recipes.

Revision ID: 3183e8a2a65f
Revises: d3e4f5a6b7c8
Create Date: 2026-07-06

Design notes
------------
* The generic `tags` array is replaced by cuisine_tags/flavor_tags/
  technique_tags plus difficulty and time_minutes — the same shape Recipe
  itself requires (§8 schema), so a tagged raw recipe carries everything
  publish needs without a human re-entering it from scratch.
* difficulty/time_minutes are nullable: a raw recipe sitting at the
  imported stage hasn't been tagged yet and has neither.
* raw_recipe_ingredients is a new table, not an array column, mirroring
  recipe_ingredients — each row is one raw ingredient line mapped to a
  catalog ingredient (nullable — an unmatched line is a valid, if
  incomplete, tagging result that a human reviewer must resolve) plus its
  essential/optional role.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "3183e8a2a65f"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None

_SKILL_LEVEL = postgresql.ENUM(
    "beginner",
    "intermediate",
    "advanced",
    name="skill_level",
    create_type=False,
)

_INGREDIENT_ROLE = postgresql.ENUM(
    "essential",
    "optional",
    name="ingredient_role",
    create_type=False,
)


def upgrade() -> None:
    op.drop_column("raw_recipes", "tags")

    op.add_column(
        "raw_recipes",
        sa.Column(
            "cuisine_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )
    op.add_column(
        "raw_recipes",
        sa.Column(
            "flavor_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )
    op.add_column(
        "raw_recipes",
        sa.Column(
            "technique_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )
    op.add_column("raw_recipes", sa.Column("difficulty", _SKILL_LEVEL, nullable=True))
    op.add_column(
        "raw_recipes", sa.Column("time_minutes", sa.Integer(), nullable=True)
    )

    op.create_table(
        "raw_recipe_ingredients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "raw_recipe_id",
            sa.String(36),
            sa.ForeignKey("raw_recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column(
            "ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", _INGREDIENT_ROLE, nullable=False),
    )
    op.create_index(
        "ix_raw_recipe_ingredients_raw_recipe_id",
        "raw_recipe_ingredients",
        ["raw_recipe_id"],
    )
    op.create_index(
        "ix_raw_recipe_ingredients_ingredient_id",
        "raw_recipe_ingredients",
        ["ingredient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_raw_recipe_ingredients_ingredient_id",
        table_name="raw_recipe_ingredients",
    )
    op.drop_index(
        "ix_raw_recipe_ingredients_raw_recipe_id",
        table_name="raw_recipe_ingredients",
    )
    op.drop_table("raw_recipe_ingredients")

    op.drop_column("raw_recipes", "time_minutes")
    op.drop_column("raw_recipes", "difficulty")
    op.drop_column("raw_recipes", "technique_tags")
    op.drop_column("raw_recipes", "flavor_tags")
    op.drop_column("raw_recipes", "cuisine_tags")

    op.add_column(
        "raw_recipes",
        sa.Column(
            "tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
    )
