"""Data transfer objects for the Cook Now feed use case (§5.3).

The feed only ever surfaces recipes classified Cook Now (§10 Step 2) — every
essential ingredient is already on hand or has a valid substitution — so
every card's badges describe *why* it's cookable now, not what's missing
entirely.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GetCookNowFeedInput:
    user_id: str
    tab: str  # "for_you" | "explore"


@dataclass(frozen=True)
class SubstitutionSuggestionOutput:
    """One essential ingredient's swap, revealed when its badge is tapped."""

    from_ingredient_id: str
    from_ingredient_name: str
    to_ingredient_id: str
    to_ingredient_name: str
    disclosure: str
    ratio_note: str | None
    confidence: float


@dataclass(frozen=True)
class RecipeBadgesOutput:
    expiring_ingredient_name: str | None
    low_stock_ingredient_name: str | None
    substitution_count: int


@dataclass(frozen=True)
class RecipeCardOutput:
    id: str
    name: str
    time_minutes: int
    difficulty: str
    cuisine_tags: list[str] = field(default_factory=list)
    badges: RecipeBadgesOutput = field(
        default_factory=lambda: RecipeBadgesOutput(None, None, 0)
    )
    substitutions: list[SubstitutionSuggestionOutput] = field(default_factory=list)
