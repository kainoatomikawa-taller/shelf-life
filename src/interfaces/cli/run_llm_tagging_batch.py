"""Batch job entry point — runs the one-time LLM tagging pass (§8) over
every raw recipe currently sitting at the imported stage.

This is the composition root for the job: the one place that wires the
concrete Postgres repositories and Anthropic client to the use case's
abstract dependencies. Composition roots are the deliberate exception to
"interfaces must not import infrastructure" — dependency injection has to
assemble the graph somewhere. Every other file in interfaces/ depends only
on application/.

Usage:
    python -m src.interfaces.cli.run_llm_tagging_batch

Intended to run on a schedule (cron, a one-off ops invocation) — never at
request time, which is exactly why it lives here and not behind an HTTP
route.
"""

from __future__ import annotations

import asyncio
import sys

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.use_cases.tag_staged_recipes_with_llm import (
    TagStagedRecipesWithLlmUseCase,
)
from src.infrastructure.config import settings
from src.infrastructure.llm.anthropic_recipe_tagging_client import (
    AnthropicRecipeTaggingClient,
)
from src.infrastructure.repositories.postgres_ingredient_repository import (
    PostgresIngredientRepository,
)
from src.infrastructure.repositories.postgres_raw_recipe_repository import (
    PostgresRawRecipeRepository,
)


async def run_batch(session: AsyncSession, anthropic_client: AsyncAnthropic) -> None:
    use_case = TagStagedRecipesWithLlmUseCase(
        raw_recipe_repository=PostgresRawRecipeRepository(session),
        ingredient_repository=PostgresIngredientRepository(session),
        recipe_tagging_port=AnthropicRecipeTaggingClient(
            client=anthropic_client,
            model=settings.recipe_tagging_model,
            poll_interval_seconds=settings.recipe_tagging_batch_poll_seconds,
        ),
    )
    output = await use_case.execute()

    print(f"Tagged {len(output.tagged)} raw recipe(s).")
    for raw_recipe in output.tagged:
        unmatched = sum(1 for i in raw_recipe.tagged_ingredients if not i.matched)
        print(f"  {raw_recipe.id} ({raw_recipe.raw_name}): {unmatched} unmatched")

    if output.failed:
        print(f"Failed to tag {len(output.failed)} raw recipe(s):", file=sys.stderr)
        for failure in output.failed:
            print(f"  {failure.raw_recipe_id}: {failure.reason}", file=sys.stderr)


async def _main() -> None:
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with Session() as session, session.begin():
            async with AsyncAnthropic() as anthropic_client:
                await run_batch(session, anthropic_client)
    except Exception as exc:
        print(f"LLM tagging batch failed: {exc}", file=sys.stderr)
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
