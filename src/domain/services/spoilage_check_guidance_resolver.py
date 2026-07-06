"""SpoilageCheckGuidanceResolver domain service.

Maps an ingredient category to short, ingredient-appropriate smell/look/
texture checks. Surfaced alongside a "past estimate — check it" status so a
beginner has a concrete way to judge the item instead of tossing it purely
because an estimate has elapsed.
"""

from __future__ import annotations

from src.domain.value_objects.ingredient_category import IngredientCategory
from src.domain.value_objects.spoilage_check_tip import SpoilageCheckTip

_DEFAULT_TIP = SpoilageCheckTip(
    smell="Sour, sulfurous, or otherwise 'off' odors are the clearest warning sign.",
    look="Check for mold spots, sliminess, or an unexpected color change.",
    texture="A slick or tacky film, or noticeable mushiness, means toss it.",
)


class SpoilageCheckGuidanceResolver:
    """Maps an ingredient category to its spoilage-check tip."""

    _TIPS: dict[IngredientCategory, SpoilageCheckTip] = {
        IngredientCategory.PERISHABLE_FRIDGE: _DEFAULT_TIP,
        IngredientCategory.PERISHABLE_COUNTER: SpoilageCheckTip(
            smell="A fermented or musty smell means it's past its best.",
            look="Look for mold, dark soft spots, or noticeably shriveled skin.",
            texture="If it's gone mushy or is leaking liquid, don't eat it.",
        ),
        IngredientCategory.FROZEN: SpoilageCheckTip(
            smell="A sour or rancid smell after thawing means it's gone bad.",
            look=(
                "Heavy ice crystals or gray-brown patches are freezer burn — "
                "lower quality, but still safe."
            ),
            texture="A slimy or sticky texture after thawing means discard it.",
        ),
        IngredientCategory.PANTRY: SpoilageCheckTip(
            smell="A musty or rancid smell (oils, nuts, grains) means it's turned.",
            look="Look for mold, insect activity, or a bulging or rusted can or lid.",
            texture="Clumping in dry goods usually means moisture damage.",
        ),
        IngredientCategory.SPICE: SpoilageCheckTip(
            smell="Still safe — a faded aroma just means it's weaker, not dangerous.",
            look="Faded color is normal and only means less potent flavor.",
            texture="Texture doesn't affect safety; use more if flavor seems weak.",
        ),
    }

    def resolve(self, category: IngredientCategory) -> SpoilageCheckTip:
        return self._TIPS.get(category, _DEFAULT_TIP)
