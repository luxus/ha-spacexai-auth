"""Shared SpaceXAI / xAI Grok OAuth helpers for Home Assistant integrations.

Phase A is a pure Python library (no Home Assistant domain or config flow).
Each integration (jev conversation, xAI TTS, …) owns its Config Flow UI and
imports this package:

    from ha_spacexai_auth import (
        CLIENT_ID,
        SCOPES,
        TOKEN_URL,
        DeviceAuthorization,
        PkcePair,
        SpaceXaiAuthError,
        SpaceXaiAuthExpired,
        SpaceXaiEntitlementError,
        TokenSet,
        authorization_headers,
        generate_pkce,
        poll_token,
        refresh_access_token,
        start_device_auth,
        token_data_updates,
    )

Public names also include RFC-style aliases ``request_device_code`` and
``poll_device_token``.
"""

from __future__ import annotations

from .const import (
    AUTH_METHOD_API_KEY,
    AUTH_METHOD_OAUTH,
    AUTH_METHODS,
    AUTHORIZATION_URL,
    CLIENT_ID,
    CODE_CHALLENGE_METHOD,
    DEVICE_AUTHORIZATION_URL,
    DEVICE_GRANT_TYPE,
    DISCOVERY_URL,
    ISSUER,
    REFERRER,
    REFRESH_GRANT_TYPE,
    REVOKE_URL,
    SCOPE_LIST,
    SCOPES,
    TOKEN_URL,
    AuthMethod,
)
from .device_flow import (
    DeviceAuthorization,
    PkcePair,
    generate_pkce,
    poll_device_token,
    poll_token,
    request_device_code,
    start_device_auth,
)
from .errors import SpaceXaiAuthError, SpaceXaiAuthExpired, SpaceXaiEntitlementError
from .headers import authorization_headers
from .refresh import refresh_access_token
from .store import TokenSet, token_data_updates

__version__ = "0.1.0"

__all__ = [
    "AUTH_METHODS",
    "AUTH_METHOD_API_KEY",
    "AUTH_METHOD_OAUTH",
    "AUTHORIZATION_URL",
    "CLIENT_ID",
    "CODE_CHALLENGE_METHOD",
    "DEVICE_AUTHORIZATION_URL",
    "DEVICE_GRANT_TYPE",
    "DISCOVERY_URL",
    "ISSUER",
    "REFERRER",
    "REFRESH_GRANT_TYPE",
    "REVOKE_URL",
    "SCOPE_LIST",
    "SCOPES",
    "TOKEN_URL",
    "AuthMethod",
    "DeviceAuthorization",
    "PkcePair",
    "SpaceXaiAuthError",
    "SpaceXaiAuthExpired",
    "SpaceXaiEntitlementError",
    "TokenSet",
    "authorization_headers",
    "generate_pkce",
    "poll_device_token",
    "poll_token",
    "refresh_access_token",
    "request_device_code",
    "start_device_auth",
    "token_data_updates",
]
