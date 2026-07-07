"""TagStagedRecipesWithLlm use case — the one-time LLM tagging pipeline.

Runs a single batch LLM pass over every raw recipe still sitting at the
imported stage: cuisine/flavor/technique tags, difficulty, time, and a
catalog mapping (or explicit unmatched flag) plus essential/optional role
per ingredient (§8 AC1-3). It is a batch job over staging, never a
per-request/per-user call (§8 AC4) — the only place that decides *when* to
call the LLM is whoever schedules a run of this use case (see
src/interfaces/cli/run_llm_tagging_batch.py), not a controller.

Catalog resolution is done here, not by the LLM: RecipeTaggingPort returns
each ingredient's best-guess canonical name as free text, and this use case
looks that name up against the real ingredient catalog via
IngredientRepository.find_by_name_or_alias. A name with no exact match is
left unmatched (ingredient_id=None) rather than guessed at — an incorrect
silent match is worse than a flagged gap a human reviewer can fix.

A raw recipe whose LLM call fails, or whose result doesn't satisfy
RawRecipe.tag()'s invariants (e.g. no ingredients at all), is recorded as a
failure and left at the imported stage so it can be retried on the next
run; it never blocks the rest of the batch.
"""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import (
    TaggingFailureOutput,
    TagStagedRecipesWithLlmOutput,
)
from src.application.dtos.recipe_tagging_dtos import (
    RecipeTaggingFailure,
    RecipeTaggingRequest,
)
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.application.ports.recipe_tagging_port import RecipeTaggingPort
from src.domain.exceptions import DomainError
from src.domain.repositories.ingredient_repository import IngredientRepository
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient


class TagStagedRecipesWithLlmUseCase:
    """The batch job: run the LLM tagging pass over every imported raw recipe."""

    def __init__(
        self,
        raw_recipe_repository: RawRecipeRepository,
        ingredient_repository: IngredientRepository,
        recipe_tagging_port: RecipeTaggingPort,
    ) -> None:
        self._raw_recipe_repository = raw_recipe_repository
        self._ingredient_repository = ingredient_repository
        self._recipe_tagging_port = recipe_tagging_port

    async def execute(self) -> TagStagedRecipesWithLlmOutput:
        raw_recipes = await self._raw_recipe_repository.list_by_stage(
            PipelineStage.IMPORTED
        )
        if not raw_recipes:
            return TagStagedRecipesWithLlmOutput()

        raw_recipes_by_id = {r.id: r for r in raw_recipes}
        requests = [
            RecipeTaggingRequest(
                raw_recipe_id=r.id,
                raw_name=r.raw_name,
                raw_ingredients=r.raw_ingredients,
                raw_method=r.raw_method,
            )
            for r in raw_recipes
        ]
        results = await self._recipe_tagging_port.tag_recipes(requests)

        tagged = []
        failed = []
        for result in results:
            raw_recipe = raw_recipes_by_id.get(result.raw_recipe_id)
            if raw_recipe is None:
                continue

            if isinstance(result, RecipeTaggingFailure):
                failed.append(
                    TaggingFailureOutput(
                        raw_recipe_id=result.raw_recipe_id, reason=result.reason
                    )
                )
                continue

            try:
                tagged_ingredients = [
                    TaggedIngredient(
                        raw_text=ingredient.raw_text,
                        ingredient_id=await self._resolve_ingredient_id(
                            ingredient.catalog_name
                        ),
                        role=IngredientRole(ingredient.role),
                    )
                    for ingredient in result.ingredients
                ]
                raw_recipe.tag(
                    tagged_ingredients=tagged_ingredients,
                    difficulty=SkillLevel(result.difficulty),
                    time_minutes=result.time_minutes,
                    cuisine_tags=result.cuisine_tags,
                    flavor_tags=result.flavor_tags,
                    technique_tags=result.technique_tags,
                )
            except (DomainError, ValueError) as exc:
                failed.append(
                    TaggingFailureOutput(
                        raw_recipe_id=result.raw_recipe_id, reason=str(exc)
                    )
                )
                continue

            await self._raw_recipe_repository.update(raw_recipe)
            tagged.append(RawRecipeMapper.to_output(raw_recipe))

        return TagStagedRecipesWithLlmOutput(tagged=tagged, failed=failed)

    async def _resolve_ingredient_id(self, catalog_name: str | None) -> str | None:
        if not catalog_name:
            return None
        matches = await self._ingredient_repository.find_by_name_or_alias(
            catalog_name
        )
        return matches[0].id if matches else None
