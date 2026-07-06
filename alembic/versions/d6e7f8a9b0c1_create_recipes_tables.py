"""Create recipes and recipe_ingredients tables (§8 schema).

Revision ID: d6e7f8a9b0c1
Revises: c4d5e6f7a8b9
Create Date: 2026-07-06

Design notes
------------
* recipe_ingredients is a join table, one row per (recipe, ingredient) pair,
  tagged essential or optional (AC1). This is the input allergen/diet tag
  derivation reads from — recipes carries no allergen_tags/diet_tags columns
  because those are computed from the ingredient catalog, never stored.
* difficulty reuses the skill_level enum type created for users, since a
  recipe's difficulty is compared directly against a user's skill_level.
* FKs use ON DELETE CASCADE so removing a recipe or catalog ingredient
  cleans up dependent recipe_ingredients rows.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "d6e7f8a9b0c1"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None

_INGREDIENT_ROLE = postgresql.ENUM(
    "essential",
    "optional",
    name="ingredient_role",
)


def upgrade() -> None:
    bind = op.get_bind()
    _INGREDIENT_ROLE.create(bind, checkfirst=True)

    op.create_table(
        "recipes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "cuisine_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "flavor_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "technique_tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "equipment_needed",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "steps",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("time_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum(
                "beginner",
                "intermediate",
                "advanced",
                name="skill_level",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "popularity_score", sa.Float(), nullable=False, server_default="0"
        ),
        sa.CheckConstraint(
            "time_minutes > 0", name="ck_recipes_time_minutes_positive"
        ),
        sa.CheckConstraint(
            "popularity_score >= 0", name="ck_recipes_popularity_score_non_negative"
        ),
    )
    op.create_index("ix_recipes_name", "recipes", ["name"])

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "recipe_id",
            sa.String(36),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum(
                "essential", "optional", name="ingredient_role", create_type=False
            ),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "recipe_id", "ingredient_id", name="uq_recipe_ingredients_pair"
        ),
    )
    op.create_index(
        "ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"]
    )
    op.create_index(
        "ix_recipe_ingredients_ingredient_id",
        "recipe_ingredients",
        ["ingredient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recipe_ingredients_ingredient_id", table_name="recipe_ingredients"
    )
    op.drop_index("ix_recipe_ingredients_recipe_id", table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index("ix_recipes_name", table_name="recipes")
    op.drop_table("recipes")

    _INGREDIENT_ROLE.drop(op.get_bind(), checkfirst=True)
