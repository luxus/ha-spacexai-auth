"""RFC 8628 device authorization grant with RFC 7636 S256 PKCE."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from ._http import HttpSession, post_form
from .const import (
    CLIENT_ID,
    CODE_CHALLENGE_METHOD,
    DEFAULT_DEVICE_POLL_INTERVAL,
    DEVICE_AUTHORIZATION_URL,
    DEVICE_GRANT_TYPE,
    REFERRER,
    SCOPES,
    SLOW_DOWN_INCREMENT,
    TOKEN_URL,
)
from .errors import SpaceXaiAuthError, SpaceXaiAuthExpired
from .store import TokenSet

SleepFn = Callable[[float], Awaitable[None]]
TimeFn = Callable[[], float]


@dataclass(frozen=True)
class PkcePair:
    """RFC 7636 PKCE verifier + S256 challenge."""

    verifier: str
    challenge: str
    method: str = CODE_CHALLENGE_METHOD


@dataclass(frozen=True)
class DeviceAuthorization:
    """RFC 8628 device authorization response plus the PKCE pair used."""

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int
    pkce: PkcePair
    expires_at: float


def generate_pkce() -> PkcePair:
    """Create a PKCE pair (S256). Verifier is 43 unreserved characters."""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PkcePair(verifier=verifier, challenge=challenge)


def _validate_verification_uri(uri: str) -> None:
    if any(ch.isascii() and ord(ch) < 32 for ch in uri):
        raise SpaceXaiAuthError("server returned invalid verification URI")
    parsed = urlsplit(uri)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}:
        return
    raise SpaceXaiAuthError("server returned unsupported verification URI scheme")


def _oauth_error(payload: Any) -> tuple[str | None, str]:
    if not isinstance(payload, Mapping):
        text = "" if payload is None else str(payload)
        return None, text
    error = payload.get("error")
    description = payload.get("error_description") or error or ""
    return (str(error) if error else None), str(description)


async def start_device_auth(
    session: HttpSession,
    *,
    pkce: PkcePair | None = None,
    client_id: str = CLIENT_ID,
    scopes: str = SCOPES,
    referrer: str = REFERRER,
    device_url: str = DEVICE_AUTHORIZATION_URL,
    time_fn: TimeFn | None = None,
) -> DeviceAuthorization:
    """POST ``/oauth2/device/code`` and return user/device codes + PKCE.

    Form fields: ``client_id``, ``scope``, ``referrer``, ``code_challenge``,
    ``code_challenge_method``.
    """
    now = (time_fn or time.time)()
    pkce = pkce or generate_pkce()
    status, payload = await post_form(
        session,
        device_url,
        {
            "client_id": client_id,
            "scope": scopes,
            "referrer": referrer,
            "code_challenge": pkce.challenge,
            "code_challenge_method": pkce.method,
        },
    )
    if status >= 400 or not isinstance(payload, Mapping):
        error, detail = _oauth_error(payload)
        raise SpaceXaiAuthError(
            f"device code request failed ({status}): {detail or payload!r}",
            error=error,
        )
    device_code = payload.get("device_code")
    user_code = payload.get("user_code")
    verification_uri = payload.get("verification_uri")
    if not device_code or not user_code or not verification_uri:
        raise SpaceXaiAuthError(
            "device code response is missing device_code, user_code, or verification_uri"
        )
    user_code_s = str(user_code)
    if not all(ch.isalnum() or ch == "-" for ch in user_code_s):
        raise SpaceXaiAuthError("server returned invalid user_code format")
    _validate_verification_uri(str(verification_uri))
    complete = payload.get("verification_uri_complete")
    if complete:
        _validate_verification_uri(str(complete))
    expires_in = int(payload.get("expires_in") or 600)
    interval = int(payload.get("interval") or DEFAULT_DEVICE_POLL_INTERVAL)
    return DeviceAuthorization(
        device_code=str(device_code),
        user_code=user_code_s,
        verification_uri=str(verification_uri),
        verification_uri_complete=str(complete) if complete else None,
        expires_in=expires_in,
        interval=max(interval, 1),
        pkce=pkce,
        expires_at=now + expires_in,
    )


async def _poll_once(
    session: HttpSession,
    device_auth: DeviceAuthorization,
    *,
    client_id: str,
    token_url: str,
    now: float,
) -> TokenSet | str:
    """Single token poll. Returns TokenSet, or ``pending`` / ``slow_down``."""
    status, payload = await post_form(
        session,
        token_url,
        {
            "grant_type": DEVICE_GRANT_TYPE,
            "client_id": client_id,
            "device_code": device_auth.device_code,
            "code_verifier": device_auth.pkce.verifier,
        },
    )
    if isinstance(payload, Mapping) and payload.get("access_token"):
        return TokenSet.from_token_response(payload, now=now)

    error, detail = _oauth_error(payload)
    if error == "authorization_pending":
        return "pending"
    if error == "slow_down":
        return "slow_down"
    if error in {"expired_token", "expired"}:
        raise SpaceXaiAuthExpired(
            detail or "device code expired; start a new device login",
            error=error,
        )
    if error == "access_denied":
        raise SpaceXaiAuthError(
            detail or "authorization denied",
            error=error,
        )
    raise SpaceXaiAuthError(
        f"device token poll failed ({status}): {detail or payload!r}",
        error=error,
    )


async def poll_token(
    session: HttpSession,
    device_auth: DeviceAuthorization,
    *,
    client_id: str = CLIENT_ID,
    token_url: str = TOKEN_URL,
    sleep: SleepFn | None = None,
    time_fn: TimeFn | None = None,
) -> TokenSet:
    """Poll ``/oauth2/token`` until authorized, denied, or expired.

    Handles RFC 8628 ``authorization_pending`` (retry), ``slow_down``
    (+5s interval), and ``expired_token``. Sleeps before the first poll.
    """
    sleep_fn: SleepFn = sleep or asyncio.sleep
    clock: TimeFn = time_fn or time.time
    interval = float(device_auth.interval)

    while True:
        await sleep_fn(interval)
        now = clock()
        if now >= device_auth.expires_at:
            raise SpaceXaiAuthExpired(
                "device code expired; start a new device login",
                error="expired_token",
            )
        result = await _poll_once(
            session,
            device_auth,
            client_id=client_id,
            token_url=token_url,
            now=now,
        )
        if isinstance(result, TokenSet):
            return result
        if result == "slow_down":
            interval += SLOW_DOWN_INCREMENT


# Original Phase A names (aliases for Helm/Vera start_device_auth / poll_token).
request_device_code = start_device_auth
poll_device_token = poll_token
