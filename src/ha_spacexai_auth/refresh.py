"""Refresh-token grant with rotation."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Mapping

from ._http import HttpSession, post_form
from .const import CLIENT_ID, REFRESH_GRANT_TYPE, TOKEN_URL
from .errors import SpaceXaiAuthError, SpaceXaiAuthExpired
from .store import TokenSet

TimeFn = Callable[[], float]


def _oauth_error(payload: Any) -> tuple[str | None, str]:
    if not isinstance(payload, Mapping):
        text = "" if payload is None else str(payload)
        return None, text
    error = payload.get("error")
    description = payload.get("error_description") or error or ""
    return (str(error) if error else None), str(description)


async def ensure_fresh(
    session: HttpSession,
    tokens: TokenSet,
    *,
    skew_seconds: float = 60,
    client_id: str = CLIENT_ID,
    token_url: str = TOKEN_URL,
    time_fn: TimeFn | None = None,
) -> TokenSet:
    """Return ``tokens``, refreshing when expiry is within ``skew_seconds``.

    Refreshes when ``expires_at - skew_seconds <= now``. If ``expires_at``
    is missing or ``None``, return ``tokens`` unchanged (no refresh).
    """
    now = (time_fn or time.time)()
    expires_at = getattr(tokens, "expires_at", None)
    if expires_at is None:
        return tokens
    if float(expires_at) - skew_seconds > now:
        return tokens
    return await refresh_access_token(
        session,
        tokens,
        client_id=client_id,
        token_url=token_url,
        time_fn=time_fn,
    )


async def refresh_access_token(
    session: HttpSession,
    tokens: TokenSet,
    *,
    client_id: str = CLIENT_ID,
    token_url: str = TOKEN_URL,
    time_fn: TimeFn | None = None,
) -> TokenSet:
    """Exchange ``refresh_token`` for a new access token.

    If the IdP omits a new refresh token (no rotation), the previous
    refresh token is kept.
    """
    if not tokens.refresh_token:
        raise SpaceXaiAuthExpired(
            "no refresh_token available; user must re-authenticate",
            error="invalid_grant",
        )
    now = (time_fn or time.time)()
    status, payload = await post_form(
        session,
        token_url,
        {
            "grant_type": REFRESH_GRANT_TYPE,
            "client_id": client_id,
            "refresh_token": tokens.refresh_token,
        },
    )
    if isinstance(payload, Mapping) and payload.get("access_token"):
        refreshed = TokenSet.from_token_response(
            payload,
            previous_refresh_token=tokens.refresh_token,
            now=now,
        )
        if refreshed.scope is None:
            refreshed.scope = tokens.scope
        return refreshed

    error, detail = _oauth_error(payload)
    if error in {"invalid_grant", "expired_token"} or status in {400, 401}:
        raise SpaceXaiAuthExpired(
            detail or "refresh token rejected; user must re-authenticate",
            error=error or "invalid_grant",
        )
    raise SpaceXaiAuthError(
        f"token refresh failed ({status}): {detail or payload!r}",
        error=error,
    )
