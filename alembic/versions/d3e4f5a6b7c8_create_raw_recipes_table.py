"""Create raw_recipes table (recipe ingestion staging).

Revision ID: d3e4f5a6b7c8
Revises: c9d0e1f2a3b4
Create Date: 2026-07-06

Design notes
------------
* raw_recipes is a standalone table, not a variant of recipes — staging
  data is untrusted (freeform source text) and must never be queryable
  alongside the reviewed production catalog.
* (source, source_recipe_id) is unique so re-running an import for the same
  source recipe fails loudly instead of creating duplicate staging rows.
* published_recipe_id is a nullable FK to recipes, set only once the
  pipeline reaches the published stage. ON DELETE SET NULL: removing the
  published Recipe shouldn't cascade into losing the staging/provenance
  record of where it came from.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = "d3e4f5a6b7c8"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None

_PIPELINE_STAGE = postgresql.ENUM(
    "imported",
    "tagged",
    "approved",
    "rejected",
    "published",
    name="pipeline_stage",
)


def upgrade() -> None:
    bind = op.get_bind()
    _PIPELINE_STAGE.create(bind, checkfirst=True)

    op.create_table(
        "raw_recipes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_recipe_id", sa.String(255), nullable=False),
        sa.Column("license", sa.String(128), nullable=False),
        sa.Column("raw_name", sa.String(255), nullable=False),
        sa.Column(
            "raw_ingredients",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "raw_method",
            ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("raw_attribution", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "imported",
                "tagged",
                "approved",
                "rejected",
                "published",
                name="pipeline_stage",
                create_type=False,
            ),
            nullable=False,
            server_default="imported",
        ),
        sa.Column(
            "tags",
            ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
        sa.Column(
            "published_recipe_id",
            sa.String(36),
            sa.ForeignKey("recipes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "source", "source_recipe_id", name="uq_raw_recipes_source_pair"
        ),
    )
    op.create_index("ix_raw_recipes_source", "raw_recipes", ["source"])
    op.create_index("ix_raw_recipes_stage", "raw_recipes", ["stage"])


def downgrade() -> None:
    op.drop_index("ix_raw_recipes_stage", table_name="raw_recipes")
    op.drop_index("ix_raw_recipes_source", table_name="raw_recipes")
    op.drop_table("raw_recipes")

    _PIPELINE_STAGE.drop(op.get_bind(), checkfirst=True)
