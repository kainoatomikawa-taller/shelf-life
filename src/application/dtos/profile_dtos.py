"""Data transfer objects for profile use cases.

These are plain data contracts that cross the boundary between the interfaces
layer and the application layer. They never expose domain entities directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateProfileInput:
    user_id: str
    username: str
    display_name: str


@dataclass(frozen=True)
class ProfileOutput:
    id: str
    username: str
    display_name: str
    created_at: datetime


@dataclass(frozen=True)
class UpdateProfileInput:
    user_id: str
    username: str | None = None
    display_name: str | None = None
