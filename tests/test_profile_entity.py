"""Entity tests for Profile."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.profile import Profile
from src.domain.exceptions import ValidationError

USER_ID = "11111111-1111-1111-1111-111111111111"


def _profile(email: str | None = None) -> Profile:
    return Profile(
        id=USER_ID,
        username="Alice",
        display_name="Alice Doe",
        created_at=datetime.now(UTC),
        email=email,
    )


def test_email_defaults_to_none() -> None:
    assert _profile().email is None


def test_email_is_normalized_like_username() -> None:
    profile = _profile(email=" Alice@Example.com ")

    assert profile.email == "alice@example.com"


def test_blank_email_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        _profile(email="   ")
