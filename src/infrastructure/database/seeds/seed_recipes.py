"""Seed script — populate the Cook Now recipe catalog (§5.3).

Idempotent: re-running upserts existing rows by deterministic id, and
replaces each recipe's ingredient list wholesale so edits to
recipe_seed_data.json aren't left stranded as orphaned rows.

Usage:
    python -m src.infrastructure.database.seeds.seed_recipes

Must run AFTER seed_ingredients.py: recipe ingredients reference ingredient
rows via foreign keys, so those rows must already exist.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.config import settings
from src.infrastructure.database.models import RecipeIngredientModel, RecipeModel
from src.infrastructure.database.seeds._seed_utils import ingredient_id

_RECIPE_SEED_NAMESPACE = uuid.UUID("c7d5e4f3-6b0a-4d89-a123-fabc56789012")

_DATA_FILE = Path(__file__).parent / "recipe_seed_data.json"

_FLAVOR_DIMENSIONS = (
    "sweetness",
    "saltiness",
    "sourness",
    "bitterness",
    "spiciness",
    "umami",
)


def _recipe_id(name: str) -> str:
    return str(uuid.uuid5(_RECIPE_SEED_NAMESPACE, name.lower()))


def _recipe_ingredient_id(recipe_id: str, ingredient_name: str) -> str:
    key = f"{recipe_id}|{ingredient_name.lower()}"
    return str(uuid.uuid5(_RECIPE_SEED_NAMESPACE, key))


def _build_recipe_row(item: dict) -> dict:  # type: ignore[type-arg]
    flavor_profile = item.get("flavor_profile") or {}
    row = {
        "id": _recipe_id(item["name"]),
        "name": item["name"],
        "cuisine_tags": item.get("cuisine_tags") or [],
        "flavor_tags": item.get("flavor_tags") or [],
        "technique_tags": item.get("technique_tags") or [],
        "equipment_needed": item.get("equipment_needed") or [],
        "steps": item["steps"],
        "time_minutes": item["time_minutes"],
        "difficulty": item["difficulty"],
        "popularity_score": item.get("popularity_score", 0.0),
        # Seed recipes are written for this catalog, not imported from an
        # external source — "self-authored" is literally true, satisfying
        # the same "free to store" policy every published recipe must meet
        # (see PublishRawRecipeUseCase / License).
        "license": item.get("license", "self-authored"),
        "source_attribution": item.get(
            "source_attribution", "Shelf Life editorial team"
        ),
    }
    for dimension in _FLAVOR_DIMENSIONS:
        row[f"flavor_profile_{dimension}"] = flavor_profile.get(dimension, 0.5)
    return row


async def run_seed(session: AsyncSession) -> int:
    """Upsert all recipes and their ingredient lists. Returns recipe count."""
    payload = json.loads(_DATA_FILE.read_text())
    recipes = payload["recipes"]

    for item in recipes:
        row = _build_recipe_row(item)
        recipe_id = row["id"]
        stmt = (
            pg_insert(RecipeModel)
            .values(**row)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={k: v for k, v in row.items() if k != "id"},
            )
        )
        await session.execute(stmt)

        await session.execute(
            delete(RecipeIngredientModel).where(
                RecipeIngredientModel.recipe_id == recipe_id
            )
        )
        for ingredient in item["ingredients"]:
            await session.execute(
                pg_insert(RecipeIngredientModel).values(
                    id=_recipe_ingredient_id(recipe_id, ingredient["name"]),
                    recipe_id=recipe_id,
                    ingredient_id=ingredient_id(ingredient["name"]),
                    role=ingredient["role"],
                )
            )

    return len(recipes)


async def _main() -> None:
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with Session() as session:
            async with session.begin():
                count = await run_seed(session)
        print(f"Seeded {count} recipes.")
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
