"""Create substitutions table (§8/§5.5 schema).

Revision ID: a1b2c3d4e5f6
Revises: f4b5c6d7e8a9
Create Date: 2026-07-06

Each row represents a directed substitution suggestion: "in context C, you
can use ingredient B instead of ingredient A."  Directionality is explicit —
A→B and B→A are separate rows and may differ in ratio and impact.

Design notes
------------
* confidence is NUMERIC(4,3) — exact decimal storage guarantees that
  threshold comparisons (>= 0.8) behave deterministically.
* The unique constraint on (from, to, context) prevents duplicate advice
  for the same pair in the same cooking context.
* FKs to ingredients use ON DELETE CASCADE so removing a catalog entry
  automatically cleans up its substitution rows.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f4b5c6d7e8a9"
branch_labels = None
depends_on = None

_SUBSTITUTION_CONTEXT = postgresql.ENUM(
    "baking",
    "savory",
    "general",
    name="substitution_context",
)


def upgrade() -> None:
    _SUBSTITUTION_CONTEXT.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "substitutions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "from_ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Optional free-text: "use ¾ the amount", "1:1 replacement", etc.
        sa.Column("ratio_note", sa.Text(), nullable=True),
        sa.Column(
            "context",
            sa.Enum(
                "baking",
                "savory",
                "general",
                name="substitution_context",
                create_type=False,
            ),
            nullable=False,
        ),
        # Optional free-text: describes quality / flavour impact of the swap.
        sa.Column("impact_note", sa.Text(), nullable=True),
        # NUMERIC(4,3): exact decimal 0.000–1.000; reliable for threshold queries.
        sa.Column(
            "confidence",
            sa.Numeric(precision=4, scale=3),
            nullable=False,
        ),
        # One substitution suggestion per directed pair per context.
        sa.UniqueConstraint(
            "from_ingredient_id",
            "to_ingredient_id",
            "context",
            name="uq_substitutions_pair_context",
        ),
        sa.CheckConstraint(
            "from_ingredient_id != to_ingredient_id",
            name="ck_substitutions_no_self_reference",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_substitutions_confidence_range",
        ),
    )

    # FK-side indexes — essential for "what can I substitute for X?" queries.
    op.create_index(
        "ix_substitutions_from_ingredient_id",
        "substitutions",
        ["from_ingredient_id"],
    )
    op.create_index(
        "ix_substitutions_to_ingredient_id",
        "substitutions",
        ["to_ingredient_id"],
    )
    # B-tree on confidence supports efficient WHERE confidence >= :threshold scans.
    op.create_index(
        "ix_substitutions_confidence",
        "substitutions",
        ["confidence"],
    )


def downgrade() -> None:
    op.drop_index("ix_substitutions_confidence", table_name="substitutions")
    op.drop_index("ix_substitutions_to_ingredient_id", table_name="substitutions")
    op.drop_index("ix_substitutions_from_ingredient_id", table_name="substitutions")
    op.drop_table("substitutions")
    _SUBSTITUTION_CONTEXT.drop(op.get_bind(), checkfirst=True)
