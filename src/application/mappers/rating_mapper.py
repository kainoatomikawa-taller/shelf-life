"""Mapper between the Rating entity and its output DTO."""

from __future__ import annotations

from src.application.dtos.rating_dtos import SubmitRatingOutput
from src.domain.entities.rating import Rating


class RatingMapper:
    """Translates domain entities into transport-safe DTOs."""

    @staticmethod
    def to_output(
        rating: Rating, decrementable_ingredient_ids: list[str]
    ) -> SubmitRatingOutput:
        return SubmitRatingOutput(
            id=rating.id,
            user_id=rating.user_id,
            recipe_id=rating.recipe_id,
            stars=rating.stars,
            quick_tags=rating.quick_tags,
            made_it_at=rating.made_it_at,
            decrementable_ingredient_ids=decrementable_ingredient_ids,
        )
