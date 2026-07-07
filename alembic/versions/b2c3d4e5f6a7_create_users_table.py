"""Create users table (§8/§4.6 schema).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-06

Columns are grouped to mirror the domain split between hard constraints and
soft preferences.

Design notes
------------
* Hard constraints (allergies, diet_type) are safety-critical and never
  relaxed to produce a "close enough" recommendation.
* Soft preferences only affect ranking; flavor_profile_* and taste_vector
  flatten their respective value objects into scalar/array columns.
* taste_vector is derived from flavor_profile at creation time and drifts
  as the user rates recipes — it is never set directly by callers.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

_DIET_TYPE = postgresql.ENUM(
    "omnivore",
    "vegetarian",
    "vegan",
    "pescatarian",
    "keto",
    "paleo",
    "gluten_free",
    "dairy_free",
    "halal",
    "kosher",
    name="diet_type",
)

_SKILL_LEVEL = postgresql.ENUM(
    "beginner",
    "intermediate",
    "advanced",
    name="skill_level",
)

_BUDGET_SENSITIVITY = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="budget_sensitivity",
)


def upgrade() -> None:
    bind = op.get_bind()
    _DIET_TYPE.create(bind, checkfirst=True)
    _SKILL_LEVEL.create(bind, checkfirst=True)
    _BUDGET_SENSITIVITY.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        # --- Hard constraints — never relaxed for a recommendation.
        sa.Column(
            "allergies",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "diet_type",
            postgresql.ENUM(
                "omnivore",
                "vegetarian",
                "vegan",
                "pescatarian",
                "keto",
                "paleo",
                "gluten_free",
                "dairy_free",
                "halal",
                "kosher",
                name="diet_type",
                create_type=False,
            ),
            nullable=False,
            server_default="omnivore",
        ),
        # --- Soft preferences — affect ranking only.
        sa.Column(
            "disliked_ingredients",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "liked_cuisines",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "flavor_profile_sweetness", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column(
            "flavor_profile_saltiness", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column(
            "flavor_profile_sourness", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column(
            "flavor_profile_bitterness",
            sa.Float(),
            nullable=False,
            server_default="0.5",
        ),
        sa.Column(
            "flavor_profile_spiciness", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column(
            "flavor_profile_umami", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column(
            "skill_level",
            postgresql.ENUM(
                "beginner",
                "intermediate",
                "advanced",
                name="skill_level",
                create_type=False,
            ),
            nullable=False,
            server_default="beginner",
        ),
        sa.Column(
            "typical_time_available_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column(
            "equipment",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "budget_sensitivity",
            postgresql.ENUM(
                "low",
                "medium",
                "high",
                name="budget_sensitivity",
                create_type=False,
            ),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "adventurousness", sa.Float(), nullable=False, server_default="0.5"
        ),
        # --- Derived — seeded from flavor_profile, updated by ratings.
        sa.Column(
            "taste_vector",
            postgresql.ARRAY(sa.Float()),
            nullable=False,
            server_default=sa.text("ARRAY[0.5,0.5,0.5,0.5,0.5,0.5]::float8[]"),
        ),
        sa.CheckConstraint(
            "adventurousness >= 0 AND adventurousness <= 1",
            name="ck_users_adventurousness_range",
        ),
        sa.CheckConstraint(
            "typical_time_available_minutes > 0",
            name="ck_users_typical_time_available_positive",
        ),
    )


def downgrade() -> None:
    op.drop_table("users")
    _BUDGET_SENSITIVITY.drop(op.get_bind(), checkfirst=True)
    _SKILL_LEVEL.drop(op.get_bind(), checkfirst=True)
    _DIET_TYPE.drop(op.get_bind(), checkfirst=True)
