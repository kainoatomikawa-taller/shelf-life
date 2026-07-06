"""Seed script — populate the curated substitution knowledge base.

Idempotent: re-running upserts existing rows via the unique constraint on
(from_ingredient_id, to_ingredient_id, context).  Substitution IDs are
derived deterministically so re-runs touch the same rows.

Usage:
    python -m src.infrastructure.database.seeds.seed_substitutions

Must run AFTER seed_ingredients.py: substitutions reference ingredient rows
via foreign keys, so those rows must already exist.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.config import settings
from src.infrastructure.database.models import SubstitutionModel
from src.infrastructure.database.seeds._seed_utils import ingredient_id

# Separate namespace keeps substitution IDs distinct from ingredient IDs.
_SUBSTITUTION_SEED_NAMESPACE = uuid.UUID("b8e4d3c2-5a9b-6c78-9012-efab34567890")

_DATA_FILE = Path(__file__).parent / "substitution_seed_data.json"


def _substitution_id(from_name: str, to_name: str, context: str) -> str:
    key = f"{from_name.lower()}|{to_name.lower()}|{context}"
    return str(uuid.uuid5(_SUBSTITUTION_SEED_NAMESPACE, key))


def _build_row(item: dict) -> dict:  # type: ignore[type-arg]
    from_name: str = item["from_ingredient"]
    to_name: str = item["to_ingredient"]
    context: str = item["context"]
    return {
        "id": _substitution_id(from_name, to_name, context),
        "from_ingredient_id": ingredient_id(from_name),
        "to_ingredient_id": ingredient_id(to_name),
        "ratio_note": item.get("ratio_note"),
        "context": context,
        "impact_note": item.get("impact_note"),
        "confidence": item["confidence"],
    }


async def run_seed(session: AsyncSession) -> int:
    """Upsert all substitutions.  Returns the number of rows processed."""
    payload = json.loads(_DATA_FILE.read_text())
    substitutions = payload["substitutions"]

    for item in substitutions:
        row = _build_row(item)
        stmt = (
            pg_insert(SubstitutionModel)
            .values(**row)
            .on_conflict_do_update(
                constraint="uq_substitutions_pair_context",
                set_={k: v for k, v in row.items() if k != "id"},
            )
        )
        await session.execute(stmt)

    return len(substitutions)


async def _main() -> None:
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with Session() as session:
            async with session.begin():
                count = await run_seed(session)
        print(f"Seeded {count} substitutions.")
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
