"""RawRecipe entity.

Staging record for a recipe imported from an external source, before it is
trusted enough to enter the production Recipe catalog. Deliberately separate
from Recipe (see RecipeRepository): raw_ingredients/raw_method are freeform,
untrusted text straight from the source, not the structured, catalog-linked
RecipeIngredient list a published Recipe requires.

source/source_recipe_id/license/raw_attribution exist to answer "where did
this come from and are we allowed to publish it" before any transformation
happens — provenance that has no equivalent on Recipe once a recipe has been
reviewed and rewritten in the app's own voice.

The entity is a small state machine over PipelineStage:

    imported --tag()--> tagged --approve()--> approved --publish()--> published
                              \\--reject()--> rejected

Each transition method guards against being called out of order, so an
invalid pipeline move fails loudly in the domain layer rather than silently
corrupting staging data.

tag() carries the recipe's full production-schema candidate data — cuisine/
flavor/technique tags, difficulty, time, and a TaggedIngredient per raw
ingredient line — rather than a flat list of strings. This mirrors what
Recipe itself requires (see Recipe.__init__): the tagging stage exists to
produce that shape, whether the tagger is a human curator or a batch LLM
pass, so review/publish tooling never has to re-derive it.
"""

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import InvalidPipelineTransitionError, ValidationError
from src.domain.value_objects.pipeline_stage import PipelineStage
from src.domain.value_objects.skill_level import SkillLevel
from src.domain.value_objects.tagged_ingredient import TaggedIngredient


def _normalize_tags(tags: list[str]) -> list[str]:
    return [t.strip().lower() for t in tags if t and t.strip()]


def _clean_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line and line.strip()]


class RawRecipe:
    """A recipe imported from an external source, awaiting review."""

    def __init__(
        self,
        id: str,
        source: str,
        source_recipe_id: str,
        license: str,
        raw_name: str,
        raw_ingredients: list[str],
        raw_method: list[str],
        imported_at: datetime,
        raw_attribution: str | None = None,
        stage: PipelineStage = PipelineStage.IMPORTED,
        cuisine_tags: list[str] | None = None,
        flavor_tags: list[str] | None = None,
        technique_tags: list[str] | None = None,
        difficulty: SkillLevel | None = None,
        time_minutes: int | None = None,
        tagged_ingredients: list[TaggedIngredient] | None = None,
        review_notes: str | None = None,
        rejected_reason: str | None = None,
        published_recipe_id: str | None = None,
    ) -> None:
        if not id:
            raise ValidationError("RawRecipe id is required.")
        if not source or not source.strip():
            raise ValidationError("RawRecipe source is required.")
        if not source_recipe_id or not source_recipe_id.strip():
            raise ValidationError("RawRecipe source_recipe_id is required.")
        if not license or not license.strip():
            raise ValidationError("RawRecipe license is required.")
        if not raw_name or not raw_name.strip():
            raise ValidationError("RawRecipe raw_name cannot be empty.")
        if not any(line and line.strip() for line in raw_ingredients):
            raise ValidationError("RawRecipe must have at least one raw ingredient.")
        if not any(line and line.strip() for line in raw_method):
            raise ValidationError("RawRecipe must have at least one raw method step.")
        if not isinstance(stage, PipelineStage):
            raise ValidationError("RawRecipe stage must be a valid PipelineStage.")
        if difficulty is not None and not isinstance(difficulty, SkillLevel):
            raise ValidationError("RawRecipe difficulty must be a valid SkillLevel.")
        if time_minutes is not None and time_minutes <= 0:
            raise ValidationError(
                f"RawRecipe time_minutes must be positive, got {time_minutes}."
            )

        self._id = id
        self._source = source.strip()
        self._source_recipe_id = source_recipe_id.strip()
        self._license = license.strip()
        self._raw_name = raw_name.strip()
        self._raw_ingredients = _clean_lines(raw_ingredients)
        self._raw_method = _clean_lines(raw_method)
        self._imported_at = imported_at
        self._raw_attribution = (
            raw_attribution.strip()
            if raw_attribution and raw_attribution.strip()
            else None
        )
        self._stage = stage
        self._cuisine_tags = _normalize_tags(cuisine_tags or [])
        self._flavor_tags = _normalize_tags(flavor_tags or [])
        self._technique_tags = _normalize_tags(technique_tags or [])
        self._difficulty = difficulty
        self._time_minutes = time_minutes
        self._tagged_ingredients = list(tagged_ingredients or [])
        self._review_notes = review_notes.strip() if review_notes else None
        self._rejected_reason = rejected_reason.strip() if rejected_reason else None
        self._published_recipe_id = published_recipe_id

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def source(self) -> str:
        return self._source

    @property
    def source_recipe_id(self) -> str:
        return self._source_recipe_id

    @property
    def license(self) -> str:
        return self._license

    @property
    def raw_name(self) -> str:
        return self._raw_name

    @property
    def raw_ingredients(self) -> list[str]:
        return list(self._raw_ingredients)

    @property
    def raw_method(self) -> list[str]:
        return list(self._raw_method)

    @property
    def raw_attribution(self) -> str | None:
        return self._raw_attribution

    @property
    def imported_at(self) -> datetime:
        return self._imported_at

    @property
    def stage(self) -> PipelineStage:
        return self._stage

    @property
    def cuisine_tags(self) -> list[str]:
        return list(self._cuisine_tags)

    @property
    def flavor_tags(self) -> list[str]:
        return list(self._flavor_tags)

    @property
    def technique_tags(self) -> list[str]:
        return list(self._technique_tags)

    @property
    def difficulty(self) -> SkillLevel | None:
        return self._difficulty

    @property
    def time_minutes(self) -> int | None:
        return self._time_minutes

    @property
    def tagged_ingredients(self) -> list[TaggedIngredient]:
        return list(self._tagged_ingredients)

    @property
    def review_notes(self) -> str | None:
        return self._review_notes

    @property
    def rejected_reason(self) -> str | None:
        return self._rejected_reason

    @property
    def published_recipe_id(self) -> str | None:
        return self._published_recipe_id

    # --- Pipeline transitions ------------------------------------------------

    def tag(
        self,
        tagged_ingredients: list[TaggedIngredient],
        difficulty: SkillLevel,
        time_minutes: int,
        cuisine_tags: list[str] | None = None,
        flavor_tags: list[str] | None = None,
        technique_tags: list[str] | None = None,
    ) -> None:
        """Attach the recipe's candidate production-schema data and advance
        imported -> tagged. An ingredient with ingredient_id=None is a
        deliberately allowed value here — see TaggedIngredient — but review
        tooling must surface it via unmatched_ingredients() rather than let
        it slip through to publish."""
        self._require_stage(PipelineStage.IMPORTED, PipelineStage.TAGGED)
        if not tagged_ingredients:
            raise ValidationError(
                "RawRecipe must have at least one tagged ingredient."
            )
        if not isinstance(difficulty, SkillLevel):
            raise ValidationError("RawRecipe difficulty must be a valid SkillLevel.")
        if time_minutes <= 0:
            raise ValidationError(
                f"RawRecipe time_minutes must be positive, got {time_minutes}."
            )
        self._tagged_ingredients = list(tagged_ingredients)
        self._difficulty = difficulty
        self._time_minutes = time_minutes
        self._cuisine_tags = _normalize_tags(cuisine_tags or [])
        self._flavor_tags = _normalize_tags(flavor_tags or [])
        self._technique_tags = _normalize_tags(technique_tags or [])
        self._stage = PipelineStage.TAGGED

    def unmatched_ingredients(self) -> list[TaggedIngredient]:
        """Tagged ingredients that couldn't be confidently mapped to the
        catalog — the queue a human reviewer needs to resolve before this
        raw recipe can be approved."""
        return [i for i in self._tagged_ingredients if not i.is_matched]

    def approve(self, review_notes: str | None = None) -> None:
        """Advance tagged -> approved, clearing the way to publish."""
        self._require_stage(PipelineStage.TAGGED, PipelineStage.APPROVED)
        self._review_notes = review_notes.strip() if review_notes else None
        self._stage = PipelineStage.APPROVED

    def reject(self, reason: str) -> None:
        """Advance tagged -> rejected. Terminal: a rejected raw recipe is
        never published."""
        self._require_stage(PipelineStage.TAGGED, PipelineStage.REJECTED)
        if not reason or not reason.strip():
            raise ValidationError("A rejection reason is required.")
        self._rejected_reason = reason.strip()
        self._stage = PipelineStage.REJECTED

    def publish(self, recipe_id: str) -> None:
        """Advance approved -> published, recording the id of the production
        Recipe this raw recipe was transformed into."""
        self._require_stage(PipelineStage.APPROVED, PipelineStage.PUBLISHED)
        if not recipe_id:
            raise ValidationError("recipe_id is required to publish a raw recipe.")
        self._published_recipe_id = recipe_id
        self._stage = PipelineStage.PUBLISHED

    def _require_stage(
        self, expected: PipelineStage, attempted: PipelineStage
    ) -> None:
        if self._stage is not expected:
            raise InvalidPipelineTransitionError(
                self._id, self._stage.value, attempted.value
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RawRecipe):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
