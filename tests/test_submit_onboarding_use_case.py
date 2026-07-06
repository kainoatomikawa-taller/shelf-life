"""Use case tests for onboarding submission, using the in-memory repository."""

import pytest

from src.application.dtos.user_dtos import FlavorProfileInput, SubmitOnboardingInput
from src.application.use_cases.submit_onboarding import SubmitOnboardingUseCase
from src.domain.value_objects.flavor_profile import FlavorProfile
from tests.fakes.in_memory_user_repository import InMemoryUserRepository


@pytest.mark.asyncio
async def test_first_submission_creates_a_user_with_defaults_for_skipped_steps() -> (
    None
):
    repo = InMemoryUserRepository()
    use_case = SubmitOnboardingUseCase(repo)

    output = await use_case.execute(SubmitOnboardingInput(user_id="user-1"))

    assert output.id == "user-1"
    assert output.diet_type == "omnivore"
    assert output.allergies == ()
    assert output.skill_level == "beginner"
    assert output.taste_vector["sweetness"] == 0.5
    assert await repo.get_by_id("user-1") is not None


@pytest.mark.asyncio
async def test_submission_persists_allergies_and_diet_as_safety_critical() -> None:
    repo = InMemoryUserRepository()
    use_case = SubmitOnboardingUseCase(repo)

    output = await use_case.execute(
        SubmitOnboardingInput(
            user_id="user-1",
            allergies=("Peanuts", "shellfish"),
            diet_type="vegan",
        )
    )

    assert output.allergies == ("peanuts", "shellfish")
    assert output.diet_type == "vegan"


@pytest.mark.asyncio
async def test_resubmission_updates_existing_user_without_resetting_taste_vector() -> (
    None
):
    repo = InMemoryUserRepository()
    use_case = SubmitOnboardingUseCase(repo)

    await use_case.execute(
        SubmitOnboardingInput(
            user_id="user-1",
            flavor_profile=FlavorProfileInput(sweetness=0.9),
        )
    )
    user = await repo.get_by_id("user-1")
    assert user is not None
    user.record_rating(FlavorProfile(sweetness=0.1), rating=1.0)
    drifted_sweetness = user.taste_vector.as_dict()["sweetness"]

    output = await use_case.execute(
        SubmitOnboardingInput(
            user_id="user-1",
            diet_type="vegetarian",
            flavor_profile=FlavorProfileInput(sweetness=0.9),
        )
    )

    assert output.diet_type == "vegetarian"
    # Re-submitting preferences must not overwrite the drifted taste vector.
    assert output.taste_vector["sweetness"] == drifted_sweetness


@pytest.mark.asyncio
async def test_allergy_update_immediately_affects_conflict_checks() -> None:
    """An edited allergy list must protect the very next read — recipe
    filtering must never rely on stale hard constraints (§6 AC2)."""
    repo = InMemoryUserRepository()
    use_case = SubmitOnboardingUseCase(repo)

    await use_case.execute(SubmitOnboardingInput(user_id="user-1"))
    user = await repo.get_by_id("user-1")
    assert user is not None
    assert user.has_allergy_conflict(["peanuts"]) is False

    await use_case.execute(
        SubmitOnboardingInput(user_id="user-1", allergies=("peanuts",))
    )

    user = await repo.get_by_id("user-1")
    assert user is not None
    assert user.has_allergy_conflict(["peanuts"]) is True
