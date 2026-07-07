"""PipelineStage value object.

Where a RawRecipe currently sits in the recipe ingestion pipeline: imported
raw data is tagged with candidate catalog metadata, then a human reviewer
either approves it (clearing the way to publish) or rejects it outright.
Only an approved raw recipe can be published into the production Recipe
catalog.
"""

from __future__ import annotations

from enum import Enum


class PipelineStage(str, Enum):
    IMPORTED = "imported"
    TAGGED = "tagged"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
