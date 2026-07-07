"""Fake RecipeTaggingPort for fast, isolated use case tests.

Returns a scripted outcome per raw_recipe_id rather than calling any LLM,
so TagStagedRecipesWithLlmUseCase tests exercise the use case's own
orchestration (catalog resolution, entity transitions, failure isolation)
without any real network or provider dependency.
"""

from __future__ import annotations

from src.application.dtos.recipe_tagging_dtos import (
    RecipeTaggingFailure,
    RecipeTaggingRequest,
    RecipeTaggingResult,
)
from src.application.ports.recipe_tagging_port import RecipeTaggingPort


class FakeRecipeTaggingPort(RecipeTaggingPort):
    def __init__(
        self, outcomes: dict[str, RecipeTaggingResult | RecipeTaggingFailure]
    ) -> None:
        self._outcomes = outcomes
        self.requested: list[RecipeTaggingRequest] = []

    async def tag_recipes(
        self, requests: list[RecipeTaggingRequest]
    ) -> list[RecipeTaggingResult | RecipeTaggingFailure]:
        self.requested = list(requests)
        return [self._outcomes[r.raw_recipe_id] for r in requests]
