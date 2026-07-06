"""Rating entity.

Captures a user's feedback after making a recipe (§8): a 1-5 star score,
optional quick tags describing the experience (e.g. "too salty", "easy"),
and when they made it. Recorded once per cook; not edited in place.
"""

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import ValidationError

MIN_STARS = 1
MAX_STARS = 5


def _normalize_tags(tags: list[str]) -> list[str]:
    return [t.strip().lower() for t in tags if t and t.strip()]


class Rating:
    """A user's star rating and quick tags for a recipe they made."""

    def __init__(
        self,
        id: str,
        user_id: str,
        recipe_id: str,
        stars: int,
        made_it_at: datetime,
        quick_tags: list[str] | None = None,
    ) -> None:
        if not id:
            raise ValidationError("Rating id is required.")
        if not user_id:
            raise ValidationError("Rating user_id is required.")
        if not recipe_id:
            raise ValidationError("Rating recipe_id is required.")
        if not MIN_STARS <= stars <= MAX_STARS:
            raise ValidationError(
                f"Rating stars must be between {MIN_STARS} and {MAX_STARS}, "
                f"got {stars}."
            )

        self._id = id
        self._user_id = user_id
        self._recipe_id = recipe_id
        self._stars = stars
        self._made_it_at = made_it_at
        self._quick_tags = _normalize_tags(quick_tags or [])

    # --- Identity & read-only accessors -------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def recipe_id(self) -> str:
        return self._recipe_id

    @property
    def stars(self) -> int:
        return self._stars

    @property
    def made_it_at(self) -> datetime:
        return self._made_it_at

    @property
    def quick_tags(self) -> list[str]:
        return list(self._quick_tags)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rating):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
