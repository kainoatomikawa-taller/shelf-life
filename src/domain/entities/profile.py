"""Profile entity.

The public identity attached to an authenticated user: a chosen username and
display name. `id` is the same id as the user's `auth.users.id` — a profile
doesn't have its own identity, it extends the auth identity.

The username is normalized (stripped and lowercased) in the constructor so
uniqueness can be enforced case-insensitively by a plain unique constraint —
the stored value is always already-normalized, never a mix of cases.
"""

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import ValidationError


class Profile:
    """A user's public username and display name."""

    def __init__(
        self,
        id: str,
        username: str,
        display_name: str,
        created_at: datetime,
    ) -> None:
        if not id:
            raise ValidationError("Profile id is required.")

        normalized_username = username.strip().lower()
        if not normalized_username:
            raise ValidationError("Username is required.")
        if not display_name.strip():
            raise ValidationError("Display name is required.")

        self._id = id
        self._username = normalized_username
        self._display_name = display_name
        self._created_at = created_at

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Profile):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
