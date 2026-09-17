"""Typed SpaceXAI OAuth errors."""

from __future__ import annotations


class SpaceXaiAuthError(Exception):
    """OAuth or token-handling failure.

    ``error`` is the RFC 6749 / RFC 8628 ``error`` code when the IdP
    returned one (``authorization_pending``, ``invalid_grant``, …).
    """

    def __init__(self, message: str, *, error: str | None = None) -> None:
        super().__init__(message)
        self.error = error


class SpaceXaiAuthExpired(SpaceXaiAuthError):
    """Device code or refresh token is no longer valid; user must re-auth."""


class SpaceXaiEntitlementError(SpaceXaiAuthError):
    """Token is missing a required Grok/SpaceXAI scope or entitlement."""
