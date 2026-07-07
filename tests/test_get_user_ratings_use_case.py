"""Use case tests for GetUserRatings (session-launch auto-load)."""

from datetime import UTC, datetime

import pytest

from src.application.dtos.rating_dtos import GetUserRatingsInput
from src.application.use_cases.get_user_ratings import GetUserRatingsUseCase
from src.domain.entities.rating import Rating
from src.domain.entities.user import User
from src.domain.exceptions import UserNotFoundError
from src.domain.value_objects.hard_constraints import HardConstraints
from src.domain.value_objects.soft_preferences import SoftPreferences
from tests.fakes.in_memory_rating_repository import InMemoryRatingRepository
from tests.fakes.in_memory_user_repository import InMemoryUserRepository

USER_ID = "user-1"
OTHER_USER_ID = "user-2"


def _rating(id: str, user_id: str, made_it_at: datetime) -> Rating:
    return Rating(
        id=id,
        user_id=user_id,
        recipe_id="recipe-1",
        stars=4,
        made_it_at=made_it_at,
    )


async def _build() -> tuple[GetUserRatingsUseCase, InMemoryRatingRepository]:
    rating_repo = InMemoryRatingRepository()
    user_repo = InMemoryUserRepository()
    await user_repo.add(
        User(
            id=USER_ID,
            hard_constraints=HardConstraints(),
            preferences=SoftPreferences(),
        )
    )
    return GetUserRatingsUseCase(rating_repo, user_repo), rating_repo


@pytest.mark.asyncio
async def test_returns_only_the_given_users_ratings_most_recent_first() -> None:
    use_case, rating_repo = await _build()
    await rating_repo.add(_rating("r1", USER_ID, datetime(2026, 1, 1, tzinfo=UTC)))
    await rating_repo.add(_rating("r2", USER_ID, datetime(2026, 1, 3, tzinfo=UTC)))
    await rating_repo.add(_rating("r3", OTHER_USER_ID, datetime(2026, 1, 2, tzinfo=UTC)))

    outputs = await use_case.execute(GetUserRatingsInput(user_id=USER_ID))

    assert [o.id for o in outputs] == ["r2", "r1"]


@pytest.mark.asyncio
async def test_returns_empty_list_when_user_has_no_ratings() -> None:
    use_case, _ = await _build()

    outputs = await use_case.execute(GetUserRatingsInput(user_id=USER_ID))

    assert outputs == []


@pytest.mark.asyncio
async def test_raises_when_user_does_not_exist() -> None:
    use_case, _ = await _build()

    with pytest.raises(UserNotFoundError):
        await use_case.execute(GetUserRatingsInput(user_id="unknown-user"))
