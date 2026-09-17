"""Authorization header helpers."""

from __future__ import annotations


def authorization_headers(access_token: str) -> dict[str, str]:
    """Return ``Authorization: Bearer …`` for SpaceXAI / xAI API calls."""
    return {"Authorization": f"Bearer {access_token}"}
