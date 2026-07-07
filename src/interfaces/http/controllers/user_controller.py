"""User profile HTTP controller.

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from src.application.dtos.user_dtos import FlavorProfileInput, SubmitOnboardingInput
from src.domain.exceptions import UserNotFoundError
from src.interfaces.http.dependencies import (
    CurrentUserIdDep,
    GetUserProfileUseCaseDep,
    SubmitOnboardingUseCaseDep,
)
from src.interfaces.http.schemas import OnboardingRequest, UserProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user_id: CurrentUserIdDep,
    use_case: GetUserProfileUseCaseDep,
) -> UserProfileResponse:
    try:
        output = await use_case.execute(current_user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return UserProfileResponse(**asdict(output))


@router.put("/me/profile", response_model=UserProfileResponse)
async def submit_onboarding(
    body: OnboardingRequest,
    current_user_id: CurrentUserIdDep,
    use_case: SubmitOnboardingUseCaseDep,
) -> UserProfileResponse:
    try:
        output = await use_case.execute(
            SubmitOnboardingInput(
                user_id=current_user_id,
                allergies=tuple(body.allergies),
                diet_type=body.diet_type,
                disliked_ingredients=tuple(body.disliked_ingredients),
                liked_cuisines=tuple(body.liked_cuisines),
                flavor_profile=FlavorProfileInput(**body.flavor_profile.model_dump()),
                skill_level=body.skill_level,
                typical_time_available_minutes=body.typical_time_available_minutes,
                equipment=tuple(body.equipment),
                budget_sensitivity=body.budget_sensitivity,
                adventurousness=body.adventurousness,
            )
        )
    except ValueError as exc:  # unknown enum value / invalid value object
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return UserProfileResponse(**asdict(output))
