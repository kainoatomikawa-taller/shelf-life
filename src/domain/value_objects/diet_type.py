"""DietType value object.

The dietary pattern a user follows. This is a hard constraint: a recipe
that includes ingredients incompatible with the user's diet type must never
be served, unlike soft preferences which only affect ranking.
"""

from __future__ import annotations

from enum import Enum


class DietType(str, Enum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
