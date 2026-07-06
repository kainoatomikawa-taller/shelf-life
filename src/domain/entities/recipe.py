"""Recipe entity.

A catalog entry describing a dish: what it takes to cook it (ingredients,
equipment, time, difficulty) and how it should be matched against a user's
tastes and constraints (cuisine/flavor/technique tags). It has no knowledge
of persistence, transport, or frameworks.

allergen_tags and diet_tags are deliberately not stored fields — per §8 AC3
they must be derivable from the recipe's ingredients rather than entered by
hand, which would let them drift out of sync with the ingredient catalog.
Deriving them also puts the essential/optional flag to work rather than
leaving it purely descriptive:

* allergen_tags is the union of allergen tags across ALL ingredients,
  essential and optional. An allergy is a hard safety constraint (see
  HardConstraints.conflicts_with), so an allergen contributed only by an
  optional ingredient still counts — the recipe as written includes it.
* diet_tags is the intersection of diet tags across ESSENTIAL ingredients
  only. A diet label (e.g. "vegan") should only be disqualified by an
  ingredient the cook can't leave out; an optional non-vegan garnish
  shouldn't strip the vegan tag from a recipe that's vegan without it.

flavor_profile is the numeric counterpart to flavor_tags: the same six
FlavorProfile dimensions used for a user's declared preferences and derived
TasteVector (§4.6), so a recipe's taste match can be scored by similarity
rather than tag overlap (§10 Step 3). Defaults to neutral when unset.
"""

from __future__ import annotations

from src.domain.entities.ingredient import Ingredient
from src.domain.exceptions import IngredientNotFoundError, ValidationError
from src.domain.value_objects.flavor_profile import FlavorProfile
from src.domain.value_objects.recipe_ingredient import RecipeIngredient
from src.domain.value_objects.skill_level import SkillLevel

MIN_STARS = 1.0
MAX_STARS = 5.0
DEFAULT_POPULARITY_INCREMENT = 0.05


def _normalize_tags(tags: list[str]) -> list[str]:
    return [t.strip().lower() for t in tags if t and t.strip()]


class Recipe:
    """A catalog entry for a cookable dish."""

    def __init__(
        self,
        id: str,
        name: str,
        ingredients: list[RecipeIngredient],
        steps: list[str],
        time_minutes: int,
        difficulty: SkillLevel,
        cuisine_tags: list[str] | None = None,
        flavor_tags: list[str] | None = None,
        technique_tags: list[str] | None = None,
        equipment_needed: list[str] | None = None,
        popularity_score: float = 0.0,
        flavor_profile: FlavorProfile | None = None,
    ) -> None:
        if not id:
            raise ValidationError("Recipe id is required.")
        if not name or not name.strip():
            raise ValidationError("Recipe name cannot be empty.")
        if not ingredients:
            raise ValidationError("Recipe must have at least one ingredient.")
        if not any(i.is_essential for i in ingredients):
            raise ValidationError(
                "Recipe must have at least one essential ingredient."
            )
        if not steps or not any(s and s.strip() for s in steps):
            raise ValidationError("Recipe must have at least one step.")
        if time_minutes <= 0:
            raise ValidationError(
                f"Recipe time_minutes must be positive, got {time_minutes}."
            )
        if not isinstance(difficulty, SkillLevel):
            raise ValidationError("Recipe difficulty must be a valid SkillLevel.")
        if popularity_score < 0.0:
            raise ValidationError(
                f"Recipe popularity_score cannot be negative, got {popularity_score}."
            )

        self._id = id
        self._name = name.strip()
        self._ingredients = list(ingredients)
        self._steps = [s.strip() for s in steps if s and s.strip()]
        self._time_minutes = time_minutes
        self._difficulty = difficulty
        self._cuisine_tags = _normalize_tags(cuisine_tags or [])
        self._flavor_tags = _normalize_tags(flavor_tags or [])
        self._technique_tags = _normalize_tags(technique_tags or [])
        self._equipment_needed = _normalize_tags(equipment_needed or [])
        self._popularity_score = popularity_score
        self._flavor_profile = flavor_profile or FlavorProfile()

    # --- Identity & read-only accessors ----------------------------------------

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def ingredients(self) -> list[RecipeIngredient]:
        return list(self._ingredients)

    @property
    def steps(self) -> list[str]:
        return list(self._steps)

    @property
    def time_minutes(self) -> int:
        return self._time_minutes

    @property
    def difficulty(self) -> SkillLevel:
        return self._difficulty

    @property
    def cuisine_tags(self) -> list[str]:
        return list(self._cuisine_tags)

    @property
    def flavor_tags(self) -> list[str]:
        return list(self._flavor_tags)

    @property
    def technique_tags(self) -> list[str]:
        return list(self._technique_tags)

    @property
    def equipment_needed(self) -> list[str]:
        return list(self._equipment_needed)

    @property
    def popularity_score(self) -> float:
        return self._popularity_score

    @property
    def flavor_profile(self) -> FlavorProfile:
        return self._flavor_profile

    # --- Behaviour -------------------------------------------------------------

    def essential_ingredients(self) -> list[RecipeIngredient]:
        return [i for i in self._ingredients if i.is_essential]

    def optional_ingredients(self) -> list[RecipeIngredient]:
        return [i for i in self._ingredients if not i.is_essential]

    def record_rating(self, stars: float) -> None:
        """Nudge popularity_score up for a new cook, weighted by stars.

        Every rating is a signal someone actually made the recipe, so even
        a low-star cook counts for something; a highly-rated one counts for
        more. Popularity only ever grows here — it is a global, cumulative
        engagement signal, not a per-user preference like TasteVector.
        """
        if not (MIN_STARS <= stars <= MAX_STARS):
            raise ValidationError(
                f"stars must be between {MIN_STARS} and {MAX_STARS}, got {stars}."
            )
        self._popularity_score += DEFAULT_POPULARITY_INCREMENT * (stars / MAX_STARS)

    def derive_allergen_tags(
        self, ingredients_by_id: dict[str, Ingredient]
    ) -> list[str]:
        """Union of allergen tags across every ingredient (essential or
        optional) actually called for in this recipe. Conservative by
        design — see the module docstring.
        """
        tags: set[str] = set()
        for recipe_ingredient in self._ingredients:
            tags.update(
                self._lookup(ingredients_by_id, recipe_ingredient).allergen_tags
            )
        return sorted(tags)

    def derive_diet_tags(self, ingredients_by_id: dict[str, Ingredient]) -> list[str]:
        """Intersection of diet tags across ESSENTIAL ingredients only —
        an optional ingredient can be omitted, so it can't disqualify a
        diet label. See the module docstring.
        """
        essential = self.essential_ingredients()
        tags: set[str] | None = None
        for recipe_ingredient in essential:
            ingredient_tags = set(
                self._lookup(ingredients_by_id, recipe_ingredient).diet_tags
            )
            tags = ingredient_tags if tags is None else tags & ingredient_tags
        return sorted(tags) if tags else []

    @staticmethod
    def _lookup(
        ingredients_by_id: dict[str, Ingredient], recipe_ingredient: RecipeIngredient
    ) -> Ingredient:
        ingredient = ingredients_by_id.get(recipe_ingredient.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(recipe_ingredient.ingredient_id)
        return ingredient

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Recipe):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)
