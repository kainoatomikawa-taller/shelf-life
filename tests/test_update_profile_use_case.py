"""Use case tests for UpdateProfile (§6 AC2-5)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.profile_dtos import UpdateProfileInput
from src.application.use_cases.update_profile import UpdateProfileUseCase
from src.domain.entities.profile import Profile
from src.domain.exceptions import ProfileNotFoundError, UsernameAlreadyTakenError
from tests.fakes.in_memory_profile_repository import InMemoryProfileRepository

USER_ID = "11111111-1111-1111-1111-111111111111"
OTHER_USER_ID = "22222222-2222-2222-2222-222222222222"


async def _seed(
    repository: InMemoryProfileRepository, user_id: str, username: str
) -> None:
    await repository.add(
        Profile(
            id=user_id,
            username=username,
            display_name="Original Name",
            created_at=datetime.now(UTC),
        )
    )


@pytest.mark.asyncio
async def test_updates_display_name_only() -> None:
    repository = InMemoryProfileRepository()
    await _seed(repository, USER_ID, "alice")
    use_case = UpdateProfileUseCase(repository)

    output = await use_case.execute(
        UpdateProfileInput(user_id=USER_ID, display_name="Maya")
    )

    assert output.display_name == "Maya"
    assert output.username == "alice"


@pytest.mark.asyncio
async def test_updates_username_with_unlimited_changes_and_no_cooldown() -> None:
    repository = InMemoryProfileRepository()
    await _seed(repository, USER_ID, "alice")
    use_case = UpdateProfileUseCase(repository)

    first = await use_case.execute(
        UpdateProfileInput(user_id=USER_ID, username="alice2")
    )
    second = await use_case.execute(
        UpdateProfileInput(user_id=USER_ID, username="alice3")
    )

    assert first.username == "alice2"
    assert second.username == "alice3"


@pytest.mark.asyncio
async def test_username_change_is_normalized_case_insensitively() -> None:
    repository = InMemoryProfileRepository()
    await _seed(repository, USER_ID, "alice")
    use_case = UpdateProfileUseCase(repository)

    output = await use_case.execute(
        UpdateProfileInput(user_id=USER_ID, username="MayaB")
    )

    assert output.username == "mayab"


@pytest.mark.asyncio
async def test_username_conflict_with_another_user_is_rejected() -> None:
    repository = InMemoryProfileRepository()
    await _seed(repository, USER_ID, "alice")
    await _seed(repository, OTHER_USER_ID, "maya")
    use_case = UpdateProfileUseCase(repository)

    with pytest.raises(UsernameAlreadyTakenError):
        await use_case.execute(UpdateProfileInput(user_id=USER_ID, username="MAYA"))

    # Rejected change must not have been applied.
    unchanged = await repository.get_by_id(USER_ID)
    assert unchanged is not None
    assert unchanged.username == "alice"


@pytest.mark.asyncio
async def test_reselecting_own_current_username_is_a_no_op() -> None:
    repository = InMemoryProfileRepository()
    await _seed(repository, USER_ID, "alice")
    use_case = UpdateProfileUseCase(repository)

    output = await use_case.execute(
        UpdateProfileInput(user_id=USER_ID, username="ALICE")
    )

    assert output.username == "alice"


@pytest.mark.asyncio
async def test_raises_when_profile_does_not_exist() -> None:
    repository = InMemoryProfileRepository()
    use_case = UpdateProfileUseCase(repository)

    with pytest.raises(ProfileNotFoundError):
        await use_case.execute(UpdateProfileInput(user_id="unknown", display_name="X"))
