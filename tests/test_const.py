from __future__ import annotations

import ha_spacexai_auth as pkg
from ha_spacexai_auth import (
    AUTH_METHOD_API_KEY,
    AUTH_METHOD_OAUTH,
    AUTHORIZATION_URL,
    CLIENT_ID,
    CODE_CHALLENGE_METHOD,
    DEVICE_AUTHORIZATION_URL,
    DEVICE_GRANT_TYPE,
    DISCOVERY_URL,
    ISSUER,
    REFERRER,
    REVOKE_URL,
    SCOPE_LIST,
    SCOPES,
    TOKEN_URL,
    DeviceAuthorization,
    PkcePair,
    SpaceXaiAuthError,
    SpaceXaiAuthExpired,
    SpaceXaiEntitlementError,
    TokenSet,
    authorization_headers,
    ensure_fresh,
    generate_pkce,
    poll_device_token,
    poll_token,
    refresh_access_token,
    request_device_code,
    start_device_auth,
    token_data_updates,
)
from ha_spacexai_auth.const import (
    DEVICE_AUTHORIZATION_URL as CONST_DEVICE_URL,
)
from ha_spacexai_auth.const import TOKEN_URL as CONST_TOKEN_URL
from ha_spacexai_auth.const import REVOKE_URL as CONST_REVOKE_URL


def test_url_constants_match_discovery_and_grok_build() -> None:
    assert ISSUER == "https://auth.x.ai"
    assert DISCOVERY_URL == "https://auth.x.ai/.well-known/openid-configuration"
    assert DEVICE_AUTHORIZATION_URL == "https://auth.x.ai/oauth2/device/code"
    assert TOKEN_URL == "https://auth.x.ai/oauth2/token"
    assert REVOKE_URL == "https://auth.x.ai/oauth2/revoke"
    assert AUTHORIZATION_URL == "https://auth.x.ai/oauth2/authorize"
    assert CONST_DEVICE_URL == DEVICE_AUTHORIZATION_URL
    assert CONST_TOKEN_URL == TOKEN_URL
    assert CONST_REVOKE_URL == REVOKE_URL
    assert CLIENT_ID == "b1a00492-073a-47ea-816f-4c329264a828"
    assert REFERRER == "grok-build"
    assert DEVICE_GRANT_TYPE == "urn:ietf:params:oauth:grant-type:device_code"
    assert CODE_CHALLENGE_METHOD == "S256"
    assert SCOPES == (
        "openid profile email offline_access "
        "grok-cli:access api:access conversations:read conversations:write"
    )
    assert SCOPE_LIST == (
        "openid",
        "profile",
        "email",
        "offline_access",
        "grok-cli:access",
        "api:access",
        "conversations:read",
        "conversations:write",
    )
    assert AUTH_METHOD_OAUTH == "oauth"
    assert AUTH_METHOD_API_KEY == "api_key"


def test_public_exports() -> None:
    expected = {
        "generate_pkce",
        "request_device_code",
        "poll_device_token",
        "start_device_auth",
        "poll_token",
        "refresh_access_token",
        "TokenSet",
        "DeviceAuthorization",
        "PkcePair",
        "SpaceXaiAuthError",
        "SpaceXaiAuthExpired",
        "SpaceXaiEntitlementError",
        "token_data_updates",
        "authorization_headers",
        "ensure_fresh",
        "CLIENT_ID",
        "SCOPES",
        "TOKEN_URL",
        "ISSUER",
    }
    assert expected <= set(pkg.__all__)
    assert request_device_code is start_device_auth
    assert poll_device_token is poll_token
    assert pkg.generate_pkce is generate_pkce
    assert pkg.TokenSet is TokenSet
    assert pkg.authorization_headers is authorization_headers
    assert pkg.ensure_fresh is ensure_fresh
    assert pkg.token_data_updates is token_data_updates
    assert pkg.refresh_access_token is refresh_access_token
    assert issubclass(SpaceXaiAuthExpired, SpaceXaiAuthError)
    assert issubclass(SpaceXaiEntitlementError, SpaceXaiAuthError)
