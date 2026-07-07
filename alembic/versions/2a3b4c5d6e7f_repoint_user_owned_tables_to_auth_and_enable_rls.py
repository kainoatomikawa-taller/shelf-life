"""Repoint user-owned tables to auth.users.id and enable Row-Level Security.

Revision ID: 2a3b4c5d6e7f
Revises: 9b0c1d2e3f4a
Create Date: 2026-07-07

Prerequisite for RLS: a policy like `user_id = auth.uid()` only means
anything if `user_id` actually *is* `auth.users.id`. Before this migration,
only `profiles.id` was; `users`, `inventory_items`, `ratings`, and
`shopping_list_items` still keyed off the legacy, app-generated
`users.id` (String(36)). This migration is a clean-slate rebuild (no
production data predates it) that:

1. Repoints `users.id` to `auth.users.id` (same 1:1-with-auth-identity
   pattern as `profiles` — see ProfileModel) and `inventory_items.user_id`
   / `ratings.user_id` / `shopping_list_items.user_id` to `auth.users.id`
   directly, per the convention documented in README.md.
2. Enables Row-Level Security on all five user-owned tables (`profiles`,
   `users`, `inventory_items`, `ratings`, `shopping_list_items`), each with
   SELECT/INSERT/UPDATE/DELETE policies scoping rows to `auth.uid()`.

Requires the target database to already have a real `auth.users` table
(true for Supabase-provisioned Postgres; false for the plain local
docker-compose `db` service — same caveat as 9b0c1d2e3f4a).

IMPORTANT — RLS is only as strong as the connecting role: `FORCE ROW LEVEL
SECURITY` still exempts superusers and any role with the BYPASSRLS
attribute (Postgres never subjects those to RLS, FORCE or not). If
`DATABASE_URL`'s role is a Postgres superuser (Supabase's default `postgres`
connection often is), every policy below is a silent no-op for our backend.
Verify the connecting role is a plain, non-superuser, non-BYPASSRLS role.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2a3b4c5d6e7f"
down_revision = "9b0c1d2e3f4a"
branch_labels = None
depends_on = None

_OWNER_POLICY_TABLES = (
    ("profiles", "id"),
    ("users", "id"),
    ("inventory_items", "user_id"),
    ("ratings", "user_id"),
    ("shopping_list_items", "user_id"),
)


def _enable_owner_rls(table: str, id_column: str) -> None:
    """Enable RLS on `table` with SELECT/INSERT/UPDATE/DELETE policies that
    scope every row to the caller: `id_column = auth.uid()`."""
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_select_own ON {table} "
        f"FOR SELECT USING ({id_column} = auth.uid())"
    )
    op.execute(
        f"CREATE POLICY {table}_insert_own ON {table} "
        f"FOR INSERT WITH CHECK ({id_column} = auth.uid())"
    )
    op.execute(
        f"CREATE POLICY {table}_update_own ON {table} "
        f"FOR UPDATE USING ({id_column} = auth.uid()) "
        f"WITH CHECK ({id_column} = auth.uid())"
    )
    op.execute(
        f"CREATE POLICY {table}_delete_own ON {table} "
        f"FOR DELETE USING ({id_column} = auth.uid())"
    )


def _disable_owner_rls(table: str) -> None:
    for cmd in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS {table}_{cmd}_own ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def upgrade() -> None:
    # Drop children before the table they FK into.
    op.drop_table("shopping_list_items")
    op.drop_table("ratings")
    op.drop_table("inventory_items")
    op.drop_table("users")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
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
        sa.Column("adventurousness", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column(
            "taste_vector",
            postgresql.ARRAY(sa.Float()),
            nullable=False,
            server_default=sa.text("ARRAY[0.5,0.5,0.5,0.5,0.5,0.5]::float8[]"),
        ),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "adventurousness >= 0 AND adventurousness <= 1",
            name="ck_users_adventurousness_range",
        ),
        sa.CheckConstraint(
            "typical_time_available_minutes > 0",
            name="ck_users_typical_time_available_positive",
        ),
    )

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
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
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="false"),
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
    op.create_index("ix_inventory_items_user_id", "inventory_items", ["user_id"])
    op.create_index(
        "ix_inventory_items_ingredient_id", "inventory_items", ["ingredient_id"]
    )

    op.create_table(
        "ratings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
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
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("made_it_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_recipe_id", "ratings", ["recipe_id"])

    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.String(36),
            sa.ForeignKey("ingredients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_recipe_ids",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quantity_needed_amount", sa.Float(), nullable=True),
        sa.Column("quantity_needed_unit", sa.String(32), nullable=True),
    )
    op.create_index(
        "ix_shopping_list_items_user_id", "shopping_list_items", ["user_id"]
    )
    op.create_index(
        "ix_shopping_list_items_ingredient_id",
        "shopping_list_items",
        ["ingredient_id"],
    )

    for table, id_column in _OWNER_POLICY_TABLES:
        _enable_owner_rls(table, id_column)


def downgrade() -> None:
    for table, _ in _OWNER_POLICY_TABLES:
        _disable_owner_rls(table)

    op.drop_index(
        "ix_shopping_list_items_ingredient_id", table_name="shopping_list_items"
    )
    op.drop_index("ix_shopping_list_items_user_id", table_name="shopping_list_items")
    op.drop_table("shopping_list_items")

    op.drop_index("ix_ratings_recipe_id", table_name="ratings")
    op.drop_index("ix_ratings_user_id", table_name="ratings")
    op.drop_table("ratings")

    op.drop_index("ix_inventory_items_ingredient_id", table_name="inventory_items")
    op.drop_index("ix_inventory_items_user_id", table_name="inventory_items")
    op.drop_table("inventory_items")

    op.drop_table("users")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
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
        sa.Column("adventurousness", sa.Float(), nullable=False, server_default="0.5"),
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
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="false"),
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
    op.create_index("ix_inventory_items_user_id", "inventory_items", ["user_id"])
    op.create_index(
        "ix_inventory_items_ingredient_id", "inventory_items", ["ingredient_id"]
    )

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
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("made_it_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_recipe_id", "ratings", ["recipe_id"])

    op.create_table(
        "shopping_list_items",
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
            "source_recipe_ids",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("quantity_needed_amount", sa.Float(), nullable=True),
        sa.Column("quantity_needed_unit", sa.String(32), nullable=True),
    )
    op.create_index(
        "ix_shopping_list_items_user_id", "shopping_list_items", ["user_id"]
    )
    op.create_index(
        "ix_shopping_list_items_ingredient_id",
        "shopping_list_items",
        ["ingredient_id"],
    )
