"""TokenVerifierPort interface.

Abstraction for verifying a bearer token and recovering the caller's
identity. The application layer depends on this port; the concrete
implementation — which auth provider, which signature scheme — lives in the
infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class InvalidTokenError(Exception):
    """Raised when a bearer token fails verification (expired, malformed,
    wrong signature, unknown key, or wrong issuer/audience)."""


class TokenVerifierPort(ABC):
    """A contract for verifying a bearer token and returning its subject."""

    @abstractmethod
    async def verify(self, token: str) -> str:
        """Verify the token and return the id of the user it was issued to.

        Raises InvalidTokenError if the token cannot be verified.
        """
