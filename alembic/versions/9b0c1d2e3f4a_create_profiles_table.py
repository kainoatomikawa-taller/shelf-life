"""Create profiles table, keyed by auth.users.id.

Revision ID: 9b0c1d2e3f4a
Revises: 7f2c9a1d4e6b
Create Date: 2026-07-07

Establishes the profiles table and the user-owned-table convention
documented in README.md's "Database Conventions" section: `id` is both the
primary key and a FK to `auth.users.id` (Supabase-managed, not part of our
own migrations), so a profile has no identity of its own — it extends the
auth identity with a username/display name.

`username` is stored already normalized (stripped + lowercased, enforced in
the Profile entity) so a plain unique constraint gives case-insensitive
uniqueness without a separate expression index; the check constraint below
defends that invariant against writes that bypass the application layer.

Requires the target database to already have an `auth.users` table — true
for any Supabase-provisioned Postgres, even before any user signs up. It
will fail against a plain Postgres instance with no `auth` schema (e.g. the
local docker-compose `db` service) — point DATABASE_URL at Supabase Postgres
to run it.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9b0c1d2e3f4a"
down_revision = "7f2c9a1d4e6b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "username = lower(username)", name="ck_profiles_username_lowercase"
        ),
    )


def downgrade() -> None:
    op.drop_table("profiles")
