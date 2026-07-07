"""Add email to profiles.

Revision ID: b3c4d5e6f7a8
Revises: 2a3b4c5d6e7f
Create Date: 2026-07-07

Password recovery ("forgot password") accepts a username or an email.
Supabase Auth itself is email-based and its `auth.users` table isn't part of
our migrations, so a username-based reset has nowhere server-side to resolve
the username to an email *except* a table we control. This column is that
resolution point: every profile going forward stores the account's email
alongside its username, so the (Supabase-hosted) forgot-password edge
function can look it up by username with the service-role key and trigger
Supabase's own password-reset email.

Nullable, not backfilled: unlike `recipes.license` (7f2c9a1d4e6b), there's no
safe placeholder value for an email address, so profiles created before this
migration are simply left without one — same accommodation as
`recipes.image_license`. `CreateProfileUseCase` always supplies a real value
for every profile created from here on.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3c4d5e6f7a8"
down_revision = "2a3b4c5d6e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("email", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_profiles_email", "profiles", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_profiles_email", "profiles", type_="unique")
    op.drop_column("profiles", "email")
