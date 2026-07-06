"""FlavorProfile value object.

The slider dimensions a user (or a recipe) can be scored on. Each dimension
is a float in [0.0, 1.0], where 0.5 is neutral. Soft preference — used for
ranking, never a hard eligibility filter.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from src.domain.exceptions import ValidationError

FLAVOR_DIMENSIONS = (
    "sweetness",
    "saltiness",
    "sourness",
    "bitterness",
    "spiciness",
    "umami",
)


@dataclass(frozen=True)
class FlavorProfile:
    sweetness: float = 0.5
    saltiness: float = 0.5
    sourness: float = 0.5
    bitterness: float = 0.5
    spiciness: float = 0.5
    umami: float = 0.5

    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            if not (0.0 <= value <= 1.0):
                raise ValidationError(
                    f"FlavorProfile.{f.name} must be between 0.0 and 1.0, got {value}."
                )

    def as_tuple(self) -> tuple[float, ...]:
        """Dimension values in FLAVOR_DIMENSIONS order."""
        return tuple(getattr(self, dimension) for dimension in FLAVOR_DIMENSIONS)
