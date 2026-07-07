"""Use case tests for GetMyProfile."""

from datetime import UTC, datetime

import pytest

from src.application.use_cases.get_my_profile import GetMyProfileUseCase
from src.domain.entities.profile import Profile
from src.domain.exceptions import ProfileNotFoundError
from tests.fakes.in_memory_profile_repository import InMemoryProfileRepository

USER_ID = "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_returns_the_callers_profile() -> None:
    repository = InMemoryProfileRepository()
    await repository.add(
        Profile(
            id=USER_ID,
            username="alice",
            display_name="Alice Doe",
            created_at=datetime.now(UTC),
        )
    )
    use_case = GetMyProfileUseCase(repository)

    output = await use_case.execute(USER_ID)

    assert output.id == USER_ID
    assert output.username == "alice"
    assert output.display_name == "Alice Doe"


@pytest.mark.asyncio
async def test_missing_profile_raises_not_found() -> None:
    use_case = GetMyProfileUseCase(InMemoryProfileRepository())

    with pytest.raises(ProfileNotFoundError):
        await use_case.execute(USER_ID)
