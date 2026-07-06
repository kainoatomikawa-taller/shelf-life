"""SpoilageCheckTip value object.

Short, beginner-friendly smell/look/texture guidance for deciding whether a
past-estimate item is still good, so a missed estimate doesn't default to
throwing food away unnecessarily.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpoilageCheckTip:
    smell: str
    look: str
    texture: str
