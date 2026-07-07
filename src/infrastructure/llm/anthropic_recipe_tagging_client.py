"""Anthropic implementation of RecipeTaggingPort.

Runs the one-time LLM tagging pass via the Messages Batches API rather than
one request per recipe — the whole point of §8's "batch cost, not per-user"
requirement. A single batch submission covers every raw recipe in the run;
we poll until Anthropic reports it `ended`, then stream the per-recipe
results back keyed by custom_id (=raw_recipe_id).

Each request asks the model to extract cuisine/flavor/technique tags,
difficulty, time, and a best-guess canonical name + essential/optional role
per raw ingredient line — never a catalog id. Anthropic has no visibility
into our ingredient catalog, so resolving that guess to a real Ingredient
row (or leaving it unmatched) is deliberately left to
TagStagedRecipesWithLlmUseCase in the application layer.
"""

from __future__ import annotations

import asyncio
import json

from anthropic import AsyncAnthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages import MessageBatchIndividualResponse
from anthropic.types.messages.batch_create_params import Request

from src.application.dtos.recipe_tagging_dtos import (
    LlmTaggedIngredient,
    RecipeTaggingFailure,
    RecipeTaggingRequest,
    RecipeTaggingResult,
)
from src.application.ports.recipe_tagging_port import RecipeTaggingPort

_SYSTEM_PROMPT = """You are tagging a recipe for a cooking app's catalog.

Given a recipe's name, ingredient list, and method steps, extract:
- cuisine_tags, flavor_tags, technique_tags: short lowercase descriptive tags
- difficulty: the recipe's skill level
- time_minutes: total time to make the dish, in minutes
- ingredients: for each raw ingredient line, its plain-English canonical
  grocery name (e.g. "2 cups all-purpose flour, sifted" -> "all-purpose
  flour"; omit quantity, prep notes, and brand names), or null if the line
  names no identifiable food ingredient, plus whether the recipe requires
  it (essential) or it could be left out or swapped (optional)."""

_RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "cuisine_tags": {"type": "array", "items": {"type": "string"}},
        "flavor_tags": {"type": "array", "items": {"type": "string"}},
        "technique_tags": {"type": "array", "items": {"type": "string"}},
        "difficulty": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
        },
        "time_minutes": {"type": "integer"},
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string"},
                    "catalog_name": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "role": {"type": "string", "enum": ["essential", "optional"]},
                },
                "required": ["raw_text", "catalog_name", "role"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "cuisine_tags",
        "flavor_tags",
        "technique_tags",
        "difficulty",
        "time_minutes",
        "ingredients",
    ],
    "additionalProperties": False,
}

_DEFAULT_MODEL = "claude-opus-4-8"
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_POLL_INTERVAL_SECONDS = 30.0


def _user_content(request: RecipeTaggingRequest) -> str:
    ingredients = "\n".join(f"- {line}" for line in request.raw_ingredients)
    method = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(request.raw_method))
    return (
        f"Recipe name: {request.raw_name}\n\n"
        f"Ingredients:\n{ingredients}\n\n"
        f"Method:\n{method}"
    )


class AnthropicRecipeTaggingClient(RecipeTaggingPort):
    """Batches the LLM tagging pass over staged raw recipes via Claude."""

    def __init__(
        self,
        client: AsyncAnthropic,
        model: str = _DEFAULT_MODEL,
        poll_interval_seconds: float = _DEFAULT_POLL_INTERVAL_SECONDS,
    ) -> None:
        self._client = client
        self._model = model
        self._poll_interval_seconds = poll_interval_seconds

    async def tag_recipes(
        self, requests: list[RecipeTaggingRequest]
    ) -> list[RecipeTaggingResult | RecipeTaggingFailure]:
        if not requests:
            return []

        batch = await self._client.messages.batches.create(
            requests=[
                Request(
                    custom_id=request.raw_recipe_id,
                    params=MessageCreateParamsNonStreaming(
                        model=self._model,
                        max_tokens=_DEFAULT_MAX_TOKENS,
                        system=_SYSTEM_PROMPT,
                        output_config={
                            "format": {
                                "type": "json_schema",
                                "schema": _RESULT_SCHEMA,
                            }
                        },
                        messages=[
                            {"role": "user", "content": _user_content(request)}
                        ],
                    ),
                )
                for request in requests
            ]
        )

        while batch.processing_status != "ended":
            await asyncio.sleep(self._poll_interval_seconds)
            batch = await self._client.messages.batches.retrieve(batch.id)

        outcomes: list[RecipeTaggingResult | RecipeTaggingFailure] = []
        results = await self._client.messages.batches.results(batch.id)
        async for item in results:
            outcomes.append(self._to_outcome(item))
        return outcomes

    @staticmethod
    def _to_outcome(
        item: MessageBatchIndividualResponse,
    ) -> RecipeTaggingResult | RecipeTaggingFailure:
        raw_recipe_id = item.custom_id
        result = item.result

        if result.type != "succeeded":
            return RecipeTaggingFailure(
                raw_recipe_id=raw_recipe_id, reason=f"batch result: {result.type}"
            )

        try:
            text = next(
                block.text
                for block in result.message.content
                if block.type == "text"
            )
            data = json.loads(text)
            return RecipeTaggingResult(
                raw_recipe_id=raw_recipe_id,
                cuisine_tags=data["cuisine_tags"],
                flavor_tags=data["flavor_tags"],
                technique_tags=data["technique_tags"],
                difficulty=data["difficulty"],
                time_minutes=data["time_minutes"],
                ingredients=[
                    LlmTaggedIngredient(
                        raw_text=i["raw_text"],
                        catalog_name=i["catalog_name"],
                        role=i["role"],
                    )
                    for i in data["ingredients"]
                ],
            )
        except (StopIteration, KeyError, TypeError, json.JSONDecodeError) as exc:
            return RecipeTaggingFailure(
                raw_recipe_id=raw_recipe_id,
                reason=f"unparseable tagging output: {exc}",
            )
