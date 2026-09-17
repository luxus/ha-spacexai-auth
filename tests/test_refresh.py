from __future__ import annotations

import pytest

from ha_spacexai_auth import (
    CLIENT_ID,
    TOKEN_URL,
    SpaceXaiAuthExpired,
    TokenSet,
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
