"""RecipeTaggingPort interface.

Abstraction for the one-time LLM tagging pass over staged raw recipes (see
TagStagedRecipesWithLlmUseCase). The application layer depends on this port;
the concrete implementation — which LLM, which API shape, batch vs. sync —
lives in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dtos.recipe_tagging_dtos import (
    RecipeTaggingFailure,
    RecipeTaggingRequest,
    RecipeTaggingResult,
)


class RecipeTaggingPort(ABC):
    """A batch LLM tagging contract: run every request, return one result or
    failure per request."""

    @abstractmethod
    async def tag_recipes(
        self, requests: list[RecipeTaggingRequest]
    ) -> list[RecipeTaggingResult | RecipeTaggingFailure]:
        """Run the tagging pass over a batch of staged raw recipes.

        Implementations may use a provider's async batch API internally (so
        this stays a batch cost rather than a per-recipe one — see §8 AC4),
        but must return exactly one RecipeTaggingResult or
        RecipeTaggingFailure per request, in any order.
        """
