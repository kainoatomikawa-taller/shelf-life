"""Create inventory_items table (§8 schema).

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-06

Design notes
------------
* quantity_state is a coarse in/low/out signal, not a precise amount — a
  lower-friction stock check than PantryItem's Quantity (amount + unit).
* purchase_date and printed_package_date are both optional: the freshness
  engine falls back to a conservative estimate when neither is known.
* computed_freshness_date/freshness_date_type/freshness_status are derived
  by the freshness engine (FreshnessCalculator + FreshnessStatusResolver)
  and stored rather than recomputed on every read.
* FKs to users and ingredients use ON DELETE CASCADE so removing either
  parent record cleans up dependent inventory rows.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

_QUANTITY_STATE = postgresql.ENUM(
    "in",
    "low",
    "out",
    name="quantity_state",
)

_FRESHNESS_DATE_TYPE = postgresql.ENUM(
    "package",
    "est-from-purchase",
    "est-unknown",
    name="freshness_date_type",
)

_FRESHNESS_DISPLAY_STATUS = postgresql.ENUM(
    "fresh",
    "use_soon",
    "use_now",
    "past_estimate_check_it",
    name="freshness_display_status",
)


def upgrade() -> None:
    bind = op.get_bind()
    _QUANTITY_STATE.create(bind, checkfirst=True)
    _FRESHNESS_DATE_TYPE.create(bind, checkfirst=True)
    _FRESHNESS_DISPLAY_STATUS.create(bind, checkfirst=True)

    op.create_table(
        "inventory_items",
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
            "quantity_state",
            postgresql.ENUM(
                "in", "low", "out", name="quantity_state", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "storage_location",
            postgresql.ENUM(
                "fridge",
                "counter",
                "freezer",
                "pantry",
                name="storage_location",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("printed_package_date", sa.Date(), nullable=True),
        sa.Column(
            "is_frozen", sa.Boolean(), nullable=False, server_default="false"
        ),
        # --- Derived — populated by the freshness engine, not set directly.
        sa.Column("computed_freshness_date", sa.Date(), nullable=False),
        sa.Column(
            "freshness_date_type",
            postgresql.ENUM(
                "package",
                "est-from-purchase",
                "est-unknown",
                name="freshness_date_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "freshness_status",
            postgresql.ENUM(
                "fresh",
                "use_soon",
                "use_now",
                "past_estimate_check_it",
                name="freshness_display_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_index(
        "ix_inventory_items_user_id", "inventory_items", ["user_id"]
    )
    op.create_index(
        "ix_inventory_items_ingredient_id", "inventory_items", ["ingredient_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_items_ingredient_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_user_id", table_name="inventory_items")
    op.drop_table("inventory_items")

    bind = op.get_bind()
    _FRESHNESS_DISPLAY_STATUS.drop(bind, checkfirst=True)
    _FRESHNESS_DATE_TYPE.drop(bind, checkfirst=True)
    _QUANTITY_STATE.drop(bind, checkfirst=True)
