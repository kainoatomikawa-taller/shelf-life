"""DTOs for the LLM recipe-tagging port (RecipeTaggingPort).

These describe the boundary between TagStagedRecipesWithLlmUseCase and
whatever LLM client implements the tagging pass. catalog_name on
LlmTaggedIngredient is deliberately a free-text best guess, not a catalog
id — the LLM has no way to know our internal ingredient ids, so resolving
a guess to an authoritative Ingredient row (or flagging it unmatched) is
the use case's job, via IngredientRepository.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecipeTaggingRequest:
    """One staged raw recipe to run through the LLM tagging pass."""

    raw_recipe_id: str
    raw_name: str
    raw_ingredients: list[str]
    raw_method: list[str]


@dataclass(frozen=True)
class LlmTaggedIngredient:
    """One raw ingredient line as the LLM interpreted it."""

    raw_text: str
    catalog_name: str | None
    role: str


@dataclass(frozen=True)
class RecipeTaggingResult:
    """Successful LLM tagging output for one raw recipe."""

    raw_recipe_id: str
    cuisine_tags: list[str]
    flavor_tags: list[str]
    technique_tags: list[str]
    difficulty: str
    time_minutes: int
    ingredients: list[LlmTaggedIngredient]


@dataclass(frozen=True)
class RecipeTaggingFailure:
    """A raw recipe the LLM pass could not tag — bad/refused/errored output.

    Kept separate from an exception so one bad recipe in a batch never
    aborts the rest; see TagStagedRecipesWithLlmUseCase.
    """

    raw_recipe_id: str
    reason: str
