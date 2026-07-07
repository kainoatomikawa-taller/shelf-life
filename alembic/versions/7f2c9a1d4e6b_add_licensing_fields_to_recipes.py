"""Add licensing & attribution fields to recipes.

Revision ID: 7f2c9a1d4e6b
Revises: 3183e8a2a65f
Create Date: 2026-07-06

Design notes
------------
* license/source_attribution are NOT NULL — every published recipe must
  carry proof of where it came from and under what terms (§ Licensing &
  attribution guardrails AC1). A server_default backfills any row that
  predates this column so the NOT NULL constraint can apply immediately;
  every actual write goes through PublishRawRecipeUseCase, which always
  supplies real values derived from the source RawRecipe.
* image_url/image_license/image_attribution are nullable as a set — most
  recipes have no image yet — but an image is only ever storable under its
  own valid, non-null license (AC3), enforced by RecipeImage in the domain
  layer, not by a DB constraint (an image row with a null license simply
  means "no image", same as a null image_url).
* recipe_license is a new enum type shared by both the recipe's own
  license and its image's license — the same closed, storable set (see
  License) applies to both assets.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7f2c9a1d4e6b"
down_revision = "3183e8a2a65f"
branch_labels = None
depends_on = None

_RECIPE_LICENSE = sa.Enum(
    "public-domain",
    "cc0",
    "cc-by",
    "cc-by-sa",
    "self-authored",
    name="recipe_license",
)


def upgrade() -> None:
    bind = op.get_bind()
    _RECIPE_LICENSE.create(bind, checkfirst=True)

    op.add_column(
        "recipes",
        sa.Column(
            "license",
            _RECIPE_LICENSE,
            nullable=False,
            server_default="self-authored",
        ),
    )
    op.add_column(
        "recipes",
        sa.Column(
            "source_attribution",
            sa.Text(),
            nullable=False,
            server_default="Shelf Life catalog (pre-dates attribution tracking)",
        ),
    )
    op.add_column("recipes", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column(
        "recipes",
        sa.Column(
            "image_license",
            postgresql.ENUM(
                "public-domain",
                "cc0",
                "cc-by",
                "cc-by-sa",
                "self-authored",
                name="recipe_license",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.add_column("recipes", sa.Column("image_attribution", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("recipes", "image_attribution")
    op.drop_column("recipes", "image_license")
    op.drop_column("recipes", "image_url")
    op.drop_column("recipes", "source_attribution")
    op.drop_column("recipes", "license")

    _RECIPE_LICENSE.drop(op.get_bind(), checkfirst=True)
