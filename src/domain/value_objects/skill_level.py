"""SkillLevel value object.

A user's self-reported cooking skill, used to bias recipe complexity when
ranking recommendations. Soft preference — never a hard eligibility filter.
"""

from __future__ import annotations

from enum import Enum


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
