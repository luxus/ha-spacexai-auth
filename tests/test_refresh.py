from __future__ import annotations

import pytest

from ha_spacexai_auth import (
    CLIENT_ID,
    TOKEN_URL,
    SpaceXaiAuthExpired,
    TokenSet,
    ensure_fresh,
    refresh_access_token,
)
from tests.fakes import FakeSession


def _tokens() -> TokenSet:
    return TokenSet(
        access_token="old-at",
        refresh_token="old-rt",
        expires_at=1.0,
        token_type="Bearer",
        scope="openid",
    )


async def test_refresh_rotates_refresh_token() -> None:
    session = FakeSession(
        [
            (
                200,
                {
                    "access_token": "new-at",
                    "refresh_token": "new-rt",
                    "expires_in": 120,
                    "token_type": "Bearer",
                    "scope": "openid profile",
                },
            )
        ]
    )
    refreshed = await refresh_access_token(session, _tokens(), time_fn=lambda: 10.0)
    assert refreshed.access_token == "new-at"
    assert refreshed.refresh_token == "new-rt"
    assert refreshed.expires_at == 130.0
    assert refreshed.scope == "openid profile"
    url, data, _ = session.calls[0]
    assert url == TOKEN_URL
    assert data == {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": "old-rt",
    }


async def test_refresh_keeps_old_refresh_token_when_omitted() -> None:
    session = FakeSession(
        [(200, {"access_token": "new-at", "expires_in": 60})]
    )
    refreshed = await refresh_access_token(session, _tokens(), time_fn=lambda: 0.0)
    assert refreshed.access_token == "new-at"
    assert refreshed.refresh_token == "old-rt"
    assert refreshed.scope == "openid"


async def test_refresh_invalid_grant() -> None:
    session = FakeSession([(400, {"error": "invalid_grant"})])
    with pytest.raises(SpaceXaiAuthExpired) as exc:
        await refresh_access_token(session, _tokens())
    assert exc.value.error == "invalid_grant"


async def test_refresh_without_refresh_token() -> None:
    tokens = TokenSet(
        access_token="at",
        refresh_token=None,
        expires_at=1.0,
    )
    with pytest.raises(SpaceXaiAuthExpired, match="no refresh_token"):
        await refresh_access_token(FakeSession([]), tokens)


async def test_ensure_fresh_returns_same_tokens_when_not_near_expiry() -> None:
    tokens = _tokens()
    tokens.expires_at = 1_000.0
    session = FakeSession([])
    result = await ensure_fresh(session, tokens, skew_seconds=60, time_fn=lambda: 900.0)
    assert result is tokens
    assert session.calls == []


async def test_ensure_fresh_refreshes_when_within_skew() -> None:
    tokens = _tokens()
    tokens.expires_at = 1_050.0
    session = FakeSession(
        [(200, {"access_token": "new-at", "refresh_token": "new-rt", "expires_in": 120})]
    )
    result = await ensure_fresh(session, tokens, skew_seconds=60, time_fn=lambda: 1_000.0)
    assert result.access_token == "new-at"
    assert result.refresh_token == "new-rt"
    assert result.expires_at == 1_120.0
    assert session.calls, "expected a refresh POST"


async def test_ensure_fresh_refreshes_on_skew_boundary() -> None:
    tokens = _tokens()
    tokens.expires_at = 1_060.0
    session = FakeSession([(200, {"access_token": "new-at", "expires_in": 60})])
    result = await ensure_fresh(session, tokens, skew_seconds=60, time_fn=lambda: 1_000.0)
    assert result.access_token == "new-at"
    assert session.calls


async def test_ensure_fresh_skips_refresh_without_expires_at() -> None:
    tokens = _tokens()
    tokens.expires_at = None  # type: ignore[assignment]
    session = FakeSession([])
    result = await ensure_fresh(session, tokens, time_fn=lambda: 1_000.0)
    assert result is tokens
    assert session.calls == []
