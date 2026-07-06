"""Seed script — import USDA FoodKeeper shelf-life data into the ingredient catalog.

Idempotent: re-running upserts existing rows so shelf-life values stay
current without duplicating data.  IDs are derived deterministically from
ingredient names so the same run always touches the same rows.

Usage:
    python -m src.infrastructure.database.seeds.seed_ingredients

The DATABASE_URL environment variable must point to a running PostgreSQL
instance that has had `alembic upgrade head` applied.
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
from src.infrastructure.database.models import IngredientModel

# Fixed namespace ensures ingredient IDs are stable across re-runs.
_SEED_NAMESPACE = uuid.UUID("a9f3c2e1-4b8d-5f67-89ab-cdef01234567")

_DATA_FILE = Path(__file__).parent / "foodkeeper_seed_data.json"


def _ingredient_id(name: str) -> str:
    """Deterministic UUID-5 derived from the canonical ingredient name."""
    return str(uuid.uuid5(_SEED_NAMESPACE, f"foodkeeper:{name.lower()}"))


def _build_row(item: dict) -> dict:  # type: ignore[type-arg]
    return {
        "id": _ingredient_id(item["name"]),
        "name": item["name"],
        "aliases": item.get("aliases") or [],
        "category": item["category"],
        "default_storage_location": item["default_storage_location"],
        "shelf_life_fridge_days": item.get("fridge_days"),
        "shelf_life_counter_days": item.get("counter_days"),
        "shelf_life_freezer_days": item.get("freezer_days"),
        "shelf_life_pantry_days": item.get("pantry_days"),
        "allergen_tags": item.get("allergen_tags") or [],
        "diet_tags": item.get("diet_tags") or [],
        "shelf_life_model": item.get("shelf_life_model", "spoilage"),
    }


async def run_seed(session: AsyncSession) -> int:
    """Upsert all FoodKeeper ingredients.  Returns the number of rows processed."""
    payload = json.loads(_DATA_FILE.read_text())
    ingredients = payload["ingredients"]

    for item in ingredients:
        row = _build_row(item)
        stmt = (
            pg_insert(IngredientModel)
            .values(**row)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={k: v for k, v in row.items() if k != "id"},
            )
        )
        await session.execute(stmt)

    return len(ingredients)


async def _main() -> None:
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with Session() as session:
            async with session.begin():
                count = await run_seed(session)
        print(f"Seeded {count} ingredients from FoodKeeper data.")
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
