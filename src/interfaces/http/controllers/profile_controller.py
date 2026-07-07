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

from src.application.dtos.profile_dtos import CreateProfileInput
from src.domain.exceptions import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    UsernameAlreadyTakenError,
)
from src.interfaces.http.dependencies import (
    CreateProfileUseCaseDep,
    CurrentUserIdDep,
    GetMyProfileUseCaseDep,
)
from src.interfaces.http.schemas import CreateProfileRequest, ProfileResponse

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
