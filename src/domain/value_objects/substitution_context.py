"""SubstitutionContext value object.

The cooking context in which a substitution is valid.  'general' applies
across all contexts when no narrower guidance is available.
"""

from __future__ import annotations

from enum import Enum


class SubstitutionContext(str, Enum):
    BAKING = "baking"
    SAVORY = "savory"
    GENERAL = "general"
