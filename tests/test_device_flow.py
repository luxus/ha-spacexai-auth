from __future__ import annotations

import base64
import hashlib

import pytest

from ha_spacexai_auth import (
    CLIENT_ID,
    DEVICE_AUTHORIZATION_URL,
    DEVICE_GRANT_TYPE,
    REFERRER,
    SCOPES,
    TOKEN_URL,
    DeviceAuthorization,
    PkcePair,
    SpaceXaiAuthError,
    SpaceXaiAuthExpired,
    generate_pkce,
    poll_token,
    start_device_auth,
)
from tests.fakes import FakeSession


def test_generate_pkce_s256() -> None:
    pair = generate_pkce()
    assert 43 <= len(pair.verifier) <= 128
    digest = hashlib.sha256(pair.verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    assert pair.challenge == expected
    assert pair.method == "S256"
    assert generate_pkce().verifier != pair.verifier


async def test_start_device_auth_posts_pkce_form() -> None:
    session = FakeSession(
        [
            (
                200,
                {
                    "device_code": "dev-1",
                    "user_code": "ABCD-EFGH",
                    "verification_uri": "https://auth.x.ai/device",
                    "verification_uri_complete": "https://auth.x.ai/device?user_code=ABCD-EFGH",
                    "expires_in": 300,
                    "interval": 5,
                },
            )
        ]
    )
    pkce = PkcePair(verifier="v" * 43, challenge="challenge", method="S256")
    device = await start_device_auth(session, pkce=pkce, time_fn=lambda: 1_000.0)
    assert device.device_code == "dev-1"
    assert device.user_code == "ABCD-EFGH"
    assert device.expires_at == 1_300.0
    assert device.pkce is pkce
    url, data, _headers = session.calls[0]
    assert url == DEVICE_AUTHORIZATION_URL
    assert data == {
        "client_id": CLIENT_ID,
        "scope": SCOPES,
        "referrer": REFERRER,
        "code_challenge": "challenge",
        "code_challenge_method": "S256",
    }


async def test_start_device_auth_rejects_bad_scheme() -> None:
    session = FakeSession(
        [
            (
                200,
                {
                    "device_code": "dev-1",
                    "user_code": "ABCD",
                    "verification_uri": "javascript:alert(1)",
                    "expires_in": 300,
                },
            )
        ]
    )
    with pytest.raises(SpaceXaiAuthError, match="unsupported verification URI"):
        await start_device_auth(session)


def _device(expires_at: float = 2_000.0) -> DeviceAuthorization:
    return DeviceAuthorization(
        device_code="dev-1",
        user_code="ABCD",
        verification_uri="https://auth.x.ai/device",
        verification_uri_complete=None,
        expires_in=300,
        interval=1,
        pkce=PkcePair(verifier="verifier", challenge="challenge"),
        expires_at=expires_at,
    )


async def test_poll_token_pending_then_success() -> None:
    session = FakeSession(
        [
            (400, {"error": "authorization_pending"}),
            (
                200,
                {
                    "access_token": "at",
                    "refresh_token": "rt",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": SCOPES,
                },
            ),
        ]
    )
    sleeps: list[float] = []

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    tokens = await poll_token(
        session,
        _device(),
        sleep=record_sleep,
        time_fn=lambda: 1_000.0,
    )
    assert tokens.access_token == "at"
    assert tokens.refresh_token == "rt"
    assert sleeps == [1.0, 1.0]
    _url, data, _ = session.calls[-1]
    assert data["grant_type"] == DEVICE_GRANT_TYPE
    assert data["device_code"] == "dev-1"
    assert data["code_verifier"] == "verifier"
    assert data["client_id"] == CLIENT_ID
    assert _url == TOKEN_URL


async def test_poll_token_slow_down_increases_interval() -> None:
    session = FakeSession(
        [
            (400, {"error": "slow_down"}),
            (200, {"access_token": "at", "expires_in": 10}),
        ]
    )
    sleeps: list[float] = []

    async def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    tokens = await poll_token(
        session, _device(), sleep=record_sleep, time_fn=lambda: 1_000.0
    )
    assert tokens.access_token == "at"
    assert sleeps == [1.0, 6.0]


async def test_poll_token_expired_error() -> None:
    session = FakeSession([(400, {"error": "expired_token"})])

    async def no_sleep(_: float) -> None:
        return None

    with pytest.raises(SpaceXaiAuthExpired):
        await poll_token(session, _device(), sleep=no_sleep, time_fn=lambda: 1_000.0)


async def test_poll_token_deadline() -> None:
    session = FakeSession([])

    async def no_sleep(_: float) -> None:
        return None

    with pytest.raises(SpaceXaiAuthExpired, match="expired"):
        await poll_token(
            session, _device(expires_at=500.0), sleep=no_sleep, time_fn=lambda: 1_000.0
        )
