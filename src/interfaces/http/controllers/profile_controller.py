"""Profile HTTP controller.

Thin route handlers: validate input (via schemas) -> call use case ->
serialize output. No business logic and no direct repository/DB access.

Unlike every other controller in this app, these routes derive the caller's
identity from a verified Supabase Auth bearer token (`CurrentUserIdDep`)
rather than trusting a client-supplied `user_id`.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from src.application.dtos.profile_dtos import CreateProfileInput, UpdateProfileInput
from src.domain.exceptions import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    UsernameAlreadyTakenError,
)
from src.interfaces.http.dependencies import (
    CreateProfileUseCaseDep,
    CurrentUserIdDep,
    GetMyProfileUseCaseDep,
    UpdateProfileUseCaseDep,
)
from src.interfaces.http.schemas import (
    CreateProfileRequest,
    ProfileResponse,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: CreateProfileRequest,
    current_user_id: CurrentUserIdDep,
    use_case: CreateProfileUseCaseDep,
) -> ProfileResponse:
    try:
        output = await use_case.execute(
            CreateProfileInput(
                user_id=current_user_id,
                username=body.username,
                display_name=body.display_name,
                email=body.email,
            )
        )
    except (ProfileAlreadyExistsError, UsernameAlreadyTakenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return ProfileResponse(**asdict(output))


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user_id: CurrentUserIdDep,
    use_case: GetMyProfileUseCaseDep,
) -> ProfileResponse:
    try:
        output = await use_case.execute(current_user_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ProfileResponse(**asdict(output))


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user_id: CurrentUserIdDep,
    use_case: UpdateProfileUseCaseDep,
) -> ProfileResponse:
    """Edits display_name and/or username (§6). Username changes are
    unlimited with no cooldown, but each one re-runs the case-insensitive
    uniqueness check (AC3/AC4) and is rejected on conflict (AC5)."""
    try:
        output = await use_case.execute(
            UpdateProfileInput(
                user_id=current_user_id,
                username=body.username,
                display_name=body.display_name,
            )
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except UsernameAlreadyTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return ProfileResponse(**asdict(output))
