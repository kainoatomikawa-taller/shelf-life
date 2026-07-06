"""Unit tests for the Rating entity's invariants (§8)."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.rating import Rating
from src.domain.exceptions import ValidationError


def _rating(**overrides: object) -> Rating:
    defaults: dict = dict(
        id="rating-1",
        user_id="user-1",
        recipe_id="recipe-pancakes",
        stars=4,
        made_it_at=datetime(2026, 7, 6, tzinfo=UTC),
        quick_tags=["Easy", " too salty "],
    )
    defaults.update(overrides)
    return Rating(**defaults)  # type: ignore[arg-type]


def test_captures_stars_quick_tags_and_timestamp() -> None:
    made_it_at = datetime(2026, 7, 6, tzinfo=UTC)
    rating = _rating(
        stars=5, made_it_at=made_it_at, quick_tags=["easy", "kid-approved"]
    )

    assert rating.stars == 5
    assert rating.quick_tags == ["easy", "kid-approved"]
    assert rating.made_it_at == made_it_at


def test_quick_tags_are_normalized_and_default_to_empty() -> None:
    rating = _rating(quick_tags=["Easy", " too salty ", ""])
    assert rating.quick_tags == ["easy", "too salty"]

    rating_without_tags = _rating(quick_tags=None)
    assert rating_without_tags.quick_tags == []


@pytest.mark.parametrize("stars", [0, 6, -1])
def test_rejects_stars_out_of_range(stars: int) -> None:
    with pytest.raises(ValidationError):
        _rating(stars=stars)


def test_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        _rating(id="")
    with pytest.raises(ValidationError):
        _rating(user_id="")
    with pytest.raises(ValidationError):
        _rating(recipe_id="")


def test_equality_is_by_id() -> None:
    assert _rating(id="rating-1", stars=1) == _rating(id="rating-1", stars=5)
    assert _rating(id="rating-1") != _rating(id="rating-2")
