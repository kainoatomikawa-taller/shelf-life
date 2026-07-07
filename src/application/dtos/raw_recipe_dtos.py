"""Data transfer objects for the recipe ingestion pipeline
(import -> tag -> review -> publish).

Each stage of the pipeline gets its own input/output pair so a stage can be
driven independently (e.g. by a scraper for import, a tagging tool for tag,
a human curator's console for review/publish) without any one caller needing
to know the whole pipeline's shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImportRawRecipeInput:
    source: str
    source_recipe_id: str
    license: str
    raw_name: str
    raw_ingredients: list[str]
    raw_method: list[str]
    raw_attribution: str | None = None


@dataclass(frozen=True)
class RawRecipeOutput:
    id: str
    source: str
    source_recipe_id: str
    license: str
    raw_name: str
    raw_ingredients: list[str]
    raw_method: list[str]
    stage: str
    tags: list[str] = field(default_factory=list)
    raw_attribution: str | None = None
    review_notes: str | None = None
    rejected_reason: str | None = None
    published_recipe_id: str | None = None


@dataclass(frozen=True)
class TagRawRecipeInput:
    raw_recipe_id: str
    tags: list[str]


@dataclass(frozen=True)
class ReviewRawRecipeInput:
    raw_recipe_id: str
    approve: bool
    notes: str | None = None


@dataclass(frozen=True)
class PublishRecipeIngredientInput:
    ingredient_id: str
    role: str


@dataclass(frozen=True)
class PublishRawRecipeInput:
    raw_recipe_id: str
    recipe_id: str
    name: str
    ingredients: list[PublishRecipeIngredientInput]
    steps: list[str]
    time_minutes: int
    difficulty: str
    cuisine_tags: list[str] = field(default_factory=list)
    flavor_tags: list[str] = field(default_factory=list)
    technique_tags: list[str] = field(default_factory=list)
    equipment_needed: list[str] = field(default_factory=list)
