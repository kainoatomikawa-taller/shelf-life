"""Use case tests for fetching a user's profile, using the in-memory repository."""

import pytest

from src.application.dtos.user_dtos import SubmitOnboardingInput
from src.application.use_cases.get_user_profile import GetUserProfileUseCase
from src.application.use_cases.submit_onboarding import SubmitOnboardingUseCase
from src.domain.exceptions import UserNotFoundError
from tests.fakes.in_memory_user_repository import InMemoryUserRepository


@pytest.mark.asyncio
async def test_get_profile_returns_previously_submitted_data() -> None:
    repo = InMemoryUserRepository()
    await SubmitOnboardingUseCase(repo).execute(
        SubmitOnboardingInput(user_id="user-1", diet_type="vegan")
    )

    output = await GetUserProfileUseCase(repo).execute("user-1")

    assert output.id == "user-1"
    assert output.diet_type == "vegan"


@pytest.mark.asyncio
async def test_get_profile_raises_for_unknown_user() -> None:
    repo = InMemoryUserRepository()

    with pytest.raises(UserNotFoundError):
        await GetUserProfileUseCase(repo).execute("nope")
