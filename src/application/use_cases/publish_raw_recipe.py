"""PublishRawRecipe use case — pipeline stage 4: publish.

The one place the ingestion pipeline is allowed to touch the production
Recipe catalog: transforms an approved raw recipe into a full Recipe entity
(with catalog-linked, essential/optional-tagged ingredients rather than the
raw recipe's freeform text) and persists it via RecipeRepository. The raw
recipe itself is then marked published and stamped with the resulting
recipe id, closing the loop back to its staging record for provenance.

Only a raw recipe in the approved stage can be published — RawRecipe.publish
enforces that invariant, so this use case can't accidentally promote
unreviewed or rejected staging data into the catalog.

License and source_attribution are never taken from the caller: they're
derived from the raw recipe's own recorded provenance
(RawRecipe.resolve_license/attribution_text), which is the "free to store"
enforcement point — a publisher can't launder a disallowed-license recipe
through by simply not mentioning its real license. An optional image is
accepted from the caller (e.g. a curator's own photo, or one they've
confirmed is openly licensed), but is independently license-checked before
it can be attached — see RecipeImage.
"""

from __future__ import annotations

from src.application.dtos.raw_recipe_dtos import PublishRawRecipeInput, RawRecipeOutput
from src.application.mappers.raw_recipe_mapper import RawRecipeMapper
from src.domain.entities.recipe import Recipe
from src.domain.exceptions import RawRecipeNotFoundError, UnstorableLicenseError
from src.domain.repositories.raw_recipe_repository import RawRecipeRepository
from src.domain.repositories.recipe_repository import RecipeRepository
from src.domain.value_objects.ingredient_role import IngredientRole
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_image import RecipeImage
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel


class PublishRawRecipeUseCase:
    """Stage 4 of the ingestion pipeline: publish."""

    def __init__(
        self,
        raw_recipe_repository: RawRecipeRepository,
        recipe_repository: RecipeRepository,
    ) -> None:
        self._raw_recipe_repository = raw_recipe_repository
        self._recipe_repository = recipe_repository

    async def execute(self, dto: PublishRawRecipeInput) -> RawRecipeOutput:
        raw_recipe = await self._raw_recipe_repository.get_by_id(dto.raw_recipe_id)
        if raw_recipe is None:
            raise RawRecipeNotFoundError(dto.raw_recipe_id)

        # Enforce the "free to store" policy before touching the production
        # catalog at all — see RawRecipe.resolve_license.
        license = raw_recipe.resolve_license()
        image = self._resolve_image(raw_recipe.id, dto)

        recipe = Recipe(
            id=dto.recipe_id,
            name=dto.name,
            ingredients=[
                RecipeIngredient(i.ingredient_id, IngredientRole(i.role))
                for i in dto.ingredients
            ],
            steps=dto.steps,
            time_minutes=dto.time_minutes,
            difficulty=SkillLevel(dto.difficulty),
            license=license,
            source_attribution=raw_recipe.attribution_text(),
            cuisine_tags=dto.cuisine_tags,
            flavor_tags=dto.flavor_tags,
            technique_tags=dto.technique_tags,
            equipment_needed=dto.equipment_needed,
            image=image,
        )

        # Validate the pipeline transition before writing to the production
        # catalog — a raw recipe that isn't approved must never result in a
        # persisted Recipe, even a subsequently-orphaned one. publish() also
        # re-runs the license check as a domain-level backstop.
        raw_recipe.publish(recipe.id)

        await self._recipe_repository.add(recipe)
        await self._raw_recipe_repository.update(raw_recipe)

        return RawRecipeMapper.to_output(raw_recipe)

    @staticmethod
    def _resolve_image(
        raw_recipe_id: str, dto: PublishRawRecipeInput
    ) -> RecipeImage | None:
        if dto.image is None:
            return None
        image_license = License.from_raw(dto.image.license)
        if image_license is None:
            raise UnstorableLicenseError(
                raw_recipe_id, dto.image.license, asset="image"
            )
        return RecipeImage(
            url=dto.image.url,
            license=image_license,
            attribution=dto.image.attribution,
        )
