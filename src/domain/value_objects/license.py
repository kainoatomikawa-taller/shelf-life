"""License value object.

The closed set of licenses under which recipe content (method prose,
ingredient lists) or an image may be stored and published in our catalog —
the enforcement point for the "free to store" policy: only public-domain,
openly-licensed, or self-written content reaches production (see
RawRecipe.resolve_license, Recipe.license, RecipeImage.license).

Not legal advice — this encodes the documented policy, not a legal
determination. Deliberately absent from this enum: "all rights reserved",
proprietary/unknown licenses, and the NonCommercial/NoDerivatives Creative
Commons variants (CC-BY-NC, CC-BY-ND, ...) — a NoDerivatives license would
make even our own paraphrasing of method prose a disallowed derivative
work, and NonCommercial is incompatible with a commercial catalog. Because
those are never represented as enum members, nothing in this codebase can
assign them to a published Recipe; they can only ever surface as the
unparseable raw string a RawRecipe recorded from its source.
"""

from __future__ import annotations

from enum import Enum


class License(str, Enum):
    PUBLIC_DOMAIN = "public-domain"
    CC0 = "cc0"
    CC_BY = "cc-by"
    CC_BY_SA = "cc-by-sa"
    SELF_AUTHORED = "self-authored"

    @classmethod
    def from_raw(cls, raw: str | None) -> License | None:
        """Normalize a freeform, source-reported license string (as
        captured verbatim on RawRecipe.license) to a storable License, or
        None if the source's license isn't one we're allowed to store
        under. Case/separator-insensitive; recognizes common Creative
        Commons and public-domain spellings. NonCommercial/NoDerivatives
        variants and anything unrecognized intentionally return None —
        see the module docstring.
        """
        if not raw or not raw.strip():
            return None

        key = raw.strip().lower().replace("_", "-").replace(" ", "-")
        tokens = key.split("-")

        # Reject NC/ND variants outright, before the CC-BY prefix match
        # below could otherwise mistake "cc-by-nc-4.0" for plain CC-BY.
        if "nc" in tokens or "nd" in tokens:
            return None

        aliases = {
            "public-domain": cls.PUBLIC_DOMAIN,
            "publicdomain": cls.PUBLIC_DOMAIN,
            "pd": cls.PUBLIC_DOMAIN,
            "cc0": cls.CC0,
            "cc0-1.0": cls.CC0,
            "self-authored": cls.SELF_AUTHORED,
            "self-written": cls.SELF_AUTHORED,
            "original": cls.SELF_AUTHORED,
        }
        if key in aliases:
            return aliases[key]
        if key.startswith("cc-by-sa"):
            return cls.CC_BY_SA
        if key.startswith("cc-by"):
            return cls.CC_BY
        return None
