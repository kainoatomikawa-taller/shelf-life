"""Unit tests for the RawRecipe entity's invariants and pipeline state
machine (import -> tag -> review -> publish)."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.raw_recipe import RawRecipe
from src.domain.exceptions import InvalidPipelineTransitionError, ValidationError
from src.domain.value_objects.pipeline_stage import PipelineStage

IMPORTED_AT = datetime(2026, 7, 6, tzinfo=UTC)


def _raw_recipe(**overrides: object) -> RawRecipe:
    defaults: dict = dict(
        id="raw-1",
        source="spoonacular",
        source_recipe_id="12345",
        license="CC-BY-4.0",
        raw_name="Grandma's Pancakes",
        raw_ingredients=["2 cups flour", "2 eggs"],
        raw_method=["Mix.", "Cook."],
        imported_at=IMPORTED_AT,
    )
    defaults.update(overrides)
    return RawRecipe(**defaults)  # type: ignore[arg-type]


def test_captures_source_provenance_and_license() -> None:
    raw_recipe = _raw_recipe()

    assert raw_recipe.source == "spoonacular"
    assert raw_recipe.source_recipe_id == "12345"
    assert raw_recipe.license == "CC-BY-4.0"
    assert raw_recipe.raw_ingredients == ["2 cups flour", "2 eggs"]
    assert raw_recipe.raw_method == ["Mix.", "Cook."]
    assert raw_recipe.stage == PipelineStage.IMPORTED


@pytest.mark.parametrize(
    "field_name",
    ["id", "source", "source_recipe_id", "license", "raw_name"],
)
def test_rejects_missing_required_fields(field_name: str) -> None:
    with pytest.raises(ValidationError):
        _raw_recipe(**{field_name: ""})


def test_rejects_empty_raw_ingredients_or_method() -> None:
    with pytest.raises(ValidationError):
        _raw_recipe(raw_ingredients=[])
    with pytest.raises(ValidationError):
        _raw_recipe(raw_method=["   "])


def test_tag_advances_imported_to_tagged() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["Breakfast", " Easy "])

    assert raw_recipe.stage == PipelineStage.TAGGED
    assert raw_recipe.tags == ["breakfast", "easy"]


def test_tag_from_a_non_imported_stage_raises() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])

    with pytest.raises(InvalidPipelineTransitionError):
        raw_recipe.tag(["breakfast-again"])


def test_approve_advances_tagged_to_approved() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])
    raw_recipe.approve(review_notes="Looks great.")

    assert raw_recipe.stage == PipelineStage.APPROVED
    assert raw_recipe.review_notes == "Looks great."


def test_approve_before_tagging_raises() -> None:
    raw_recipe = _raw_recipe()
    with pytest.raises(InvalidPipelineTransitionError):
        raw_recipe.approve()


def test_reject_advances_tagged_to_rejected_and_requires_a_reason() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])

    with pytest.raises(ValidationError):
        raw_recipe.reject("")

    raw_recipe.reject("Duplicate of an existing recipe.")
    assert raw_recipe.stage == PipelineStage.REJECTED
    assert raw_recipe.rejected_reason == "Duplicate of an existing recipe."


def test_rejected_raw_recipe_cannot_be_approved_or_published() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])
    raw_recipe.reject("Not a fit for the catalog.")

    with pytest.raises(InvalidPipelineTransitionError):
        raw_recipe.approve()
    with pytest.raises(InvalidPipelineTransitionError):
        raw_recipe.publish("recipe-1")


def test_publish_advances_approved_to_published() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])
    raw_recipe.approve()
    raw_recipe.publish("recipe-1")

    assert raw_recipe.stage == PipelineStage.PUBLISHED
    assert raw_recipe.published_recipe_id == "recipe-1"


def test_publish_before_approval_raises() -> None:
    raw_recipe = _raw_recipe()
    raw_recipe.tag(["breakfast"])

    with pytest.raises(InvalidPipelineTransitionError):
        raw_recipe.publish("recipe-1")


def test_equality_is_by_id() -> None:
    assert _raw_recipe(id="raw-1") == _raw_recipe(id="raw-1", raw_name="Other")
    assert _raw_recipe(id="raw-1") != _raw_recipe(id="raw-2")
