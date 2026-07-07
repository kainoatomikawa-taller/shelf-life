"""Unit tests for the License value object's "free to store" classifier."""

import pytest

from src.domain.value_objects.license import License


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("public-domain", License.PUBLIC_DOMAIN),
        ("Public Domain", License.PUBLIC_DOMAIN),
        ("pd", License.PUBLIC_DOMAIN),
        ("CC0", License.CC0),
        ("cc0-1.0", License.CC0),
        ("CC-BY-4.0", License.CC_BY),
        ("cc by 4.0", License.CC_BY),
        ("CC-BY-SA-4.0", License.CC_BY_SA),
        ("self-authored", License.SELF_AUTHORED),
        ("Self_Written", License.SELF_AUTHORED),
        ("original", License.SELF_AUTHORED),
    ],
)
def test_from_raw_recognizes_storable_licenses(raw: str, expected: License) -> None:
    assert License.from_raw(raw) is expected


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "   ",
        "all-rights-reserved",
        "proprietary",
        "unknown",
        "CC-BY-NC-4.0",
        "CC-BY-ND-4.0",
        "CC-BY-NC-SA-4.0",
    ],
)
def test_from_raw_rejects_unstorable_or_unrecognized_licenses(raw: str | None) -> None:
    assert License.from_raw(raw) is None
