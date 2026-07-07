"""TagRawRecipe use case — pipeline stage 2: tag.

Applies an already-computed tagging result — cuisine/flavor/technique tags,
difficulty, time, and a catalog-resolved-or-unmatched TaggedIngredient per
raw ingredient line — to an imported raw recipe, queuing it for human
review. This use case is deliberately source-agnostic: it doesn't care
whether the tagging result came from a human curator's tool or a batch LLM
pass (see TagStagedRecipesWithLlmUseCase), only that it already conforms to
RawRecipe.tag()'s contract.
"""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import RawRecipeOutput, TagRawRecipeInput
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.domain.exceptions import RawRecipeNotFoundError
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient


class TagRawRecipeUseCase:
    """Stage 2 of the ingestion pipeline: tag."""

    def __init__(self, raw_recipe_repository: RawRecipeRepository) -> None:
        self._raw_recipe_repository = raw_recipe_repository

    async def execute(self, dto: TagRawRecipeInput) -> RawRecipeOutput:
        raw_recipe = await self._raw_recipe_repository.get_by_id(dto.raw_recipe_id)
        if raw_recipe is None:
            raise RawRecipeNotFoundError(dto.raw_recipe_id)

        raw_recipe.tag(
            tagged_ingredients=[
                TaggedIngredient(
                    raw_text=i.raw_text,
                    ingredient_id=i.ingredient_id,
                    role=IngredientRole(i.role),
                )
                for i in dto.tagged_ingredients
            ],
            difficulty=SkillLevel(dto.difficulty),
            time_minutes=dto.time_minutes,
            cuisine_tags=dto.cuisine_tags,
            flavor_tags=dto.flavor_tags,
            technique_tags=dto.technique_tags,
        )
        await self._raw_recipe_repository.update(raw_recipe)

        return RawRecipeMapper.to_output(raw_recipe)
