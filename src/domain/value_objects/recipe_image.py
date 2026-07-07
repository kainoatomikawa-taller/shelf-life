"""RecipeImage value object.

Pairs an image URL with the License it's stored under. Requiring a
License at construction — rather than a nullable/free-text field — makes
it structurally impossible to attach an image whose license isn't in the
storable set (see License): there is no way to build a RecipeImage for a
disallowed or unverified license, so "block storage of copyrighted
images from disallowed sources" is enforced by the type itself, not just
by a check someone could forget to call.

attribution is separate from the recipe's own source_attribution (see
Recipe) because an image's provenance can differ from the recipe text's —
e.g. a self-written recipe paired with a photographer-credited CC-BY photo.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import ValidationError
from src.domain.value_objects.license import License


@dataclass(frozen=True)
class RecipeImage:
    url: str
    license: License
    attribution: str | None = None

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValidationError("RecipeImage url is required.")
        if not isinstance(self.license, License):
            raise ValidationError("RecipeImage license must be a valid License.")
