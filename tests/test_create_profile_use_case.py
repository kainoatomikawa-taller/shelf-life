"""Use case tests for CreateProfile."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.profile_dtos import CreateProfileInput
from src.application.use_cases.create_profile import CreateProfileUseCase
from src.domain.entities.profile import Profile
from src.domain.exceptions import ProfileAlreadyExistsError, UsernameAlreadyTakenError
from tests.fakes.in_memory_profile_repository import InMemoryProfileRepository

USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"


@pytest.mark.asyncio
async def test_creates_a_profile_with_a_normalized_username() -> None:
    repository = InMemoryProfileRepository()
    use_case = CreateProfileUseCase(repository)

    output = await use_case.execute(
        CreateProfileInput(
            user_id=USER_ID,
            username="Alice",
            display_name="Alice Doe",
            email="alice@example.com",
        )
    )

    assert output.id == USER_ID
    assert output.username == "alice"
    assert output.display_name == "Alice Doe"
    stored = await repository.get_by_id(USER_ID)
    assert stored is not None
    assert stored.email == "alice@example.com"


@pytest.mark.asyncio
async def test_existing_profile_for_user_raises_already_exists() -> None:
    repository = InMemoryProfileRepository()
    use_case = CreateProfileUseCase(repository)
    await use_case.execute(
        CreateProfileInput(
            user_id=USER_ID,
            username="alice",
            display_name="Alice",
            email="alice@example.com",
        )
    )

    with pytest.raises(ProfileAlreadyExistsError):
        await use_case.execute(
            CreateProfileInput(
                user_id=USER_ID,
                username="alice2",
                display_name="Alice",
                email="alice@example.com",
            )
        )


@pytest.mark.asyncio
async def test_username_taken_case_insensitively_raises() -> None:
    repository = InMemoryProfileRepository()
    use_case = CreateProfileUseCase(repository)
    await use_case.execute(
        CreateProfileInput(
            user_id=USER_ID,
            username="alice",
            display_name="Alice",
            email="alice@example.com",
        )
    )

    with pytest.raises(UsernameAlreadyTakenError):
        await use_case.execute(
            CreateProfileInput(
                user_id=OTHER_USER_ID,
                username="ALICE",
                display_name="Someone Else",
                email="someone@example.com",
            )
        )


@pytest.mark.asyncio
async def test_seeded_profile_is_visible_by_normalized_username() -> None:
    repository = InMemoryProfileRepository()

    await repository.add(
        Profile(
            id=USER_ID,
            username="Bob",
            display_name="Bob",
            created_at=datetime.now(UTC),
        )
    )

    assert await repository.get_by_username("bob") is not None
