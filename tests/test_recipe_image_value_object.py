"""Unit tests for the RecipeImage value object.

RecipeImage requires a License (not a free-text string) precisely so that
"block storage of copyrighted images from disallowed sources" is enforced
structurally — there is no way to construct one for a license that isn't
in the storable set.
"""

import pytest

from src.domain.exceptions import ValidationError
from src.domain.value_objects.license import License
from src.domain.value_objects.recipe_image import RecipeImage


def test_constructs_with_a_storable_license() -> None:
    image = RecipeImage(
        url="https://example.com/photo.jpg",
        license=License.CC_BY,
        attribution="Photo by Jane Doe",
    )
    assert image.url == "https://example.com/photo.jpg"
    assert image.license is License.CC_BY
    assert image.attribution == "Photo by Jane Doe"


def test_attribution_is_optional() -> None:
    image = RecipeImage(url="https://example.com/photo.jpg", license=License.CC0)
    assert image.attribution is None


def test_rejects_empty_url() -> None:
    with pytest.raises(ValidationError):
        RecipeImage(url="", license=License.SELF_AUTHORED)


def test_rejects_a_non_license_value() -> None:
    with pytest.raises(ValidationError):
        RecipeImage(url="https://example.com/photo.jpg", license="cc-by")  # type: ignore[arg-type]
