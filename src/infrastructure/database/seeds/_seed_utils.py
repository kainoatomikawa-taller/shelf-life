"""Shared utilities for seed scripts.

Both seed_ingredients.py and seed_substitutions.py derive ingredient IDs
from the same namespace so foreign-key lookups are always consistent.
"""

from __future__ import annotations

import uuid

# Fixed namespace — changing this would invalidate all existing seed rows.
INGREDIENT_SEED_NAMESPACE = uuid.UUID("a9f3c2e1-4b8d-5f67-89ab-cdef01234567")


def ingredient_id(name: str) -> str:
    """Deterministic UUID-5 for a canonical ingredient name."""
    return str(uuid.uuid5(INGREDIENT_SEED_NAMESPACE, f"foodkeeper:{name.lower()}"))
