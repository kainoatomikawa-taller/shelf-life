"""Proves Postgres actually enforces the RLS policies added by migration
2a3b4c5d6e7f — one user cannot read or write another user's rows.

In-memory fakes can't represent DB-enforced RLS at all, so this needs a
real Postgres. It spins up a throwaway local cluster via `initdb`/`pg_ctl`
(skipping this whole module if those binaries aren't on PATH — e.g. a
machine with no local Postgres install), stubs a minimal `auth` schema that
reproduces Supabase's real `auth.uid()`/`auth.users` shape, then runs the
*actual* shipped Alembic migrations against it — exercising the real
migration SQL, not a reimplementation — before granting a plain,
non-superuser role the table privileges Supabase's `authenticated` role
would have.

Covers the two distinct policy shapes representatively: `profiles`
(PK-style, `id = auth.uid()`) and `inventory_items` (FK-style,
`user_id = auth.uid()`). `ratings`/`shopping_list_items` share
`inventory_items`'s exact policy shape (same helper, same column pattern)
and aren't re-tested for that reason — not a coverage gap, just not
redundant.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import socket
import subprocess
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
_TEST_ROLE = "authenticated_test"
_TEST_DB = "shelflife_rls_test"

_missing_binaries = [
    b for b in ("initdb", "pg_ctl", "postgres") if shutil.which(b) is None
]

pytestmark = pytest.mark.skipif(
    bool(_missing_binaries),
    reason=f"local Postgres binaries not on PATH: {_missing_binaries}",
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run_async(coro: Any) -> Any:
    """Run an async setup step from a sync fixture. Alembic's env.py calls
    `asyncio.run()` internally, which fails inside an already-running event
    loop — so this fixture (and everything it calls) must stay sync."""
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def pg_cluster(tmp_path_factory: pytest.TempPathFactory) -> Generator[int, None, None]:
    """Starts a throwaway local Postgres cluster; yields its port."""
    data_dir = tmp_path_factory.mktemp("rls_pgdata")
    port = _free_port()

    subprocess.run(
        ["initdb", "-D", str(data_dir), "-U", "postgres", "-A", "trust", "--no-sync"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "pg_ctl",
            "start",
            "-D",
            str(data_dir),
            "-w",
            "-l",
            str(data_dir / "postgres.log"),
            "-o",
            f"-p {port} -h 127.0.0.1 -c listen_addresses=127.0.0.1",
        ],
        check=True,
        capture_output=True,
    )
    try:
        yield port
    finally:
        subprocess.run(
            ["pg_ctl", "stop", "-D", str(data_dir), "-m", "fast"],
            check=False,
            capture_output=True,
        )


@pytest.fixture(scope="module")
def rls_database(pg_cluster: int) -> Generator[dict[str, Any], None, None]:
    """Creates the test database, a stub `auth` schema, runs the real
    Alembic migrations, grants a non-superuser role table access, and seeds
    two fake `auth.users` rows. Yields the DSN and those two user ids."""
    port = pg_cluster
    admin_dsn = f"postgresql://postgres@127.0.0.1:{port}/postgres"
    db_dsn = f"postgresql://postgres@127.0.0.1:{port}/{_TEST_DB}"
    app_dsn = f"postgresql+asyncpg://postgres@127.0.0.1:{port}/{_TEST_DB}"
    role_dsn = f"postgresql://{_TEST_ROLE}@127.0.0.1:{port}/{_TEST_DB}"

    async def _setup() -> tuple[str, str]:
        admin = await asyncpg.connect(admin_dsn)
        try:
            await admin.execute(f"CREATE DATABASE {_TEST_DB}")
        finally:
            await admin.close()

        db = await asyncpg.connect(db_dsn)
        try:
            # Minimal stand-in for Supabase's real auth schema — just enough
            # for auth.uid() to work and for our FKs to auth.users(id) to
            # have somewhere to point.
            await db.execute("CREATE SCHEMA auth")
            await db.execute("CREATE TABLE auth.users (id uuid PRIMARY KEY)")
            await db.execute(
                """
                CREATE FUNCTION auth.uid() RETURNS uuid AS $$
                  SELECT nullif(
                    current_setting('request.jwt.claim.sub', true), ''
                  )::uuid
                $$ LANGUAGE sql STABLE
                """
            )
            await db.execute(
                f"CREATE ROLE {_TEST_ROLE} LOGIN NOSUPERUSER NOBYPASSRLS"
            )

            user_a = str(uuid.uuid4())
            user_b = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO auth.users (id) VALUES ($1), ($2)", user_a, user_b
            )
        finally:
            await db.close()
        return user_a, user_b

    user_a, user_b = _run_async(_setup())

    original_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = app_dsn
    try:
        alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "alembic"))
        command.upgrade(alembic_cfg, "head")
    finally:
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url

    async def _grant() -> None:
        db = await asyncpg.connect(db_dsn)
        try:
            await db.execute("GRANT USAGE ON SCHEMA public TO authenticated_test")
            await db.execute("GRANT USAGE ON SCHEMA auth TO authenticated_test")
            await db.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE "
                "ON ALL TABLES IN SCHEMA public TO authenticated_test"
            )
        finally:
            await db.close()

    _run_async(_grant())

    yield {
        "role_dsn": role_dsn,
        "admin_dsn": db_dsn,
        "user_a": user_a,
        "user_b": user_b,
    }


async def _connection_as(role_dsn: str, user_id: str) -> asyncpg.Connection:
    """A connection authenticated (for RLS purposes) as `user_id` — mirrors
    what `AuthenticatedSessionDep` does for a real request."""
    conn = await asyncpg.connect(role_dsn)
    await conn.execute(
        "SELECT set_config('request.jwt.claim.sub', $1, false)", user_id
    )
    return conn


@pytest.mark.asyncio
async def test_profiles_rls_isolates_rows_between_users(
    rls_database: dict[str, Any],
) -> None:
    role_dsn, user_a, user_b = (
        rls_database["role_dsn"],
        rls_database["user_a"],
        rls_database["user_b"],
    )
    conn_a = await _connection_as(role_dsn, user_a)
    conn_b = await _connection_as(role_dsn, user_b)
    try:
        await conn_a.execute(
            "INSERT INTO profiles (id, username, display_name) VALUES ($1, $2, $3)",
            user_a,
            "alice",
            "Alice",
        )

        assert await conn_a.fetchval(
            "SELECT username FROM profiles WHERE id = $1", user_a
        ) == "alice"

        # B can't see A's row at all.
        assert (
            await conn_b.fetchval("SELECT username FROM profiles WHERE id = $1", user_a)
            is None
        )
        assert await conn_b.fetchval("SELECT count(*) FROM profiles") == 0

        # B's UPDATE/DELETE against A's row touch zero rows.
        update_result = await conn_b.execute(
            "UPDATE profiles SET display_name = 'hacked' WHERE id = $1", user_a
        )
        assert update_result == "UPDATE 0"
        delete_result = await conn_b.execute(
            "DELETE FROM profiles WHERE id = $1", user_a
        )
        assert delete_result == "DELETE 0"
        assert await conn_a.fetchval(
            "SELECT display_name FROM profiles WHERE id = $1", user_a
        ) == "Alice"

        # B can't INSERT a profile claiming to be A's id.
        with pytest.raises(asyncpg.exceptions.PostgresError):
            await conn_b.execute(
                "INSERT INTO profiles (id, username, display_name) "
                "VALUES ($1, $2, $3)",
                user_a,
                "impersonator",
                "Not Alice",
            )
    finally:
        await conn_a.close()
        await conn_b.close()


@pytest.mark.asyncio
async def test_inventory_items_rls_isolates_rows_between_users(
    rls_database: dict[str, Any],
) -> None:
    role_dsn, user_a, user_b = (
        rls_database["role_dsn"],
        rls_database["user_a"],
        rls_database["user_b"],
    )
    conn_a = await _connection_as(role_dsn, user_a)
    conn_b = await _connection_as(role_dsn, user_b)
    try:
        # Seed a catalog ingredient as the admin (superuser bypasses RLS,
        # and ingredients aren't user-owned/RLS-protected anyway).
        admin = await asyncpg.connect(rls_database["admin_dsn"])
        ingredient_id = str(uuid.uuid4())
        try:
            await admin.execute(
                "INSERT INTO ingredients "
                "(id, name, category, default_storage_location, shelf_life_model) "
                "VALUES ($1, 'Flour', 'pantry', 'pantry', 'spoilage')",
                ingredient_id,
            )
        finally:
            await admin.close()

        item_id = str(uuid.uuid4())
        await conn_a.execute(
            """
            INSERT INTO inventory_items (
                id, user_id, ingredient_id, quantity_state, storage_location,
                computed_freshness_date, freshness_date_type, freshness_status,
                added_at
            ) VALUES ($1, $2, $3, 'in', 'pantry', now(), 'est-unknown', 'fresh', now())
            """,
            item_id,
            user_a,
            ingredient_id,
        )

        assert await conn_a.fetchval(
            "SELECT count(*) FROM inventory_items WHERE id = $1", item_id
        ) == 1

        # B's "my inventory" query — no manual user_id filter needed, RLS
        # already scopes it — returns nothing of A's.
        assert await conn_b.fetchval("SELECT count(*) FROM inventory_items") == 0

        update_result = await conn_b.execute(
            "UPDATE inventory_items SET notes = 'hacked' WHERE id = $1", item_id
        )
        assert update_result == "UPDATE 0"
        delete_result = await conn_b.execute(
            "DELETE FROM inventory_items WHERE id = $1", item_id
        )
        assert delete_result == "DELETE 0"

        # B can't INSERT an inventory item claiming to belong to A.
        with pytest.raises(asyncpg.exceptions.PostgresError):
            await conn_b.execute(
                """
                INSERT INTO inventory_items (
                    id, user_id, ingredient_id, quantity_state, storage_location,
                    computed_freshness_date, freshness_date_type, freshness_status,
                    added_at
                ) VALUES (
                    $1, $2, $3, 'in', 'pantry', now(), 'est-unknown', 'fresh', now()
                )
                """,
                str(uuid.uuid4()),
                user_a,
                ingredient_id,
            )
    finally:
        await conn_a.close()
        await conn_b.close()
