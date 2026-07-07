"""Add shelf_life_model column to ingredients.

Revision ID: f4b5c6d7e8a9
Revises: e3a1f2c4d5b6
Create Date: 2026-07-06

Adds an explicit model flag so the application can communicate to users
whether a shelf-life expiry means "unsafe to eat" (spoilage) or
"has lost peak quality/potency" (potency, used for all spices).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f4b5c6d7e8a9"
down_revision = "e3a1f2c4d5b6"
branch_labels = None
depends_on = None

_SHELF_LIFE_MODEL_TYPE = postgresql.ENUM(
    "spoilage",
    "potency",
    name="shelf_life_model_type",
)


def upgrade() -> None:
    _SHELF_LIFE_MODEL_TYPE.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "ingredients",
        sa.Column(
            "shelf_life_model",
            postgresql.ENUM(
                "spoilage", "potency", name="shelf_life_model_type", create_type=False
            ),
            nullable=False,
            server_default="spoilage",
        ),
    )


def downgrade() -> None:
    op.drop_column("ingredients", "shelf_life_model")
    _SHELF_LIFE_MODEL_TYPE.drop(op.get_bind(), checkfirst=True)
