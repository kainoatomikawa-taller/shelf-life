"""Add flavor_profile columns to recipes (§10 schema).

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-06

Design notes
------------
* Flattens FlavorProfile into six scalar columns, the same convention
  already used for users.flavor_profile_* — needed so a recipe's taste
  match can be scored by numeric similarity against a user's taste vector
  (§10 Step 3) rather than by flavor_tags overlap alone.
* All six default to 0.5 (neutral), matching FlavorProfile's own default,
  so existing recipe rows remain valid without a backfill.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None

_DIMENSIONS = (
    "sweetness",
    "saltiness",
    "sourness",
    "bitterness",
    "spiciness",
    "umami",
)


def upgrade() -> None:
    for dimension in _DIMENSIONS:
        op.add_column(
            "recipes",
            sa.Column(
                f"flavor_profile_{dimension}",
                sa.Float(),
                nullable=False,
                server_default="0.5",
            ),
        )


def downgrade() -> None:
    for dimension in _DIMENSIONS:
        op.drop_column("recipes", f"flavor_profile_{dimension}")
