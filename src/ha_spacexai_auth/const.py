"""Pinned SpaceXAI / xAI Grok OAuth constants.

Verify against xai-org/grok-build:
``crates/codegen/xai-grok-login/src/config.rs``
(``XAI_OAUTH2_ISSUER``, public ``client_id``, ``default_oauth2_scopes``,
``DEFAULT_OAUTH2_REFERRER``).

Discovery (``https://auth.x.ai/.well-known/openid-configuration``) currently
advertises the same device/token/revoke paths recorded here. This library pins
the URLs so Home Assistant integrations do not need a discovery round-trip.

The Helm/Vera scope pin matches the eight-scope set used by luxus/pi-xai
(``XAI_OAUTH_SCOPE``). grok-build ``default_oauth2_scopes()`` also currently
includes ``workspaces:read`` and ``workspaces:write``; those are intentionally
not requested here unless the contract is updated.
"""

from __future__ import annotations

from typing import Final, Literal

# Issuer + well-known discovery (https://auth.x.ai/.well-known/openid-configuration)
ISSUER: Final = "https://auth.x.ai"
DISCOVERY_URL: Final = f"{ISSUER}/.well-known/openid-configuration"

DEVICE_AUTHORIZATION_URL: Final = f"{ISSUER}/oauth2/device/code"
TOKEN_URL: Final = f"{ISSUER}/oauth2/token"
REVOKE_URL: Final = f"{ISSUER}/oauth2/revoke"
AUTHORIZATION_URL: Final = f"{ISSUER}/oauth2/authorize"

# Public grok-build OAuth2 client (no secret). Obfuscated in config.rs as:
# obfstr!("b1a00492-073a-47ea-816f-4c329264a828")
CLIENT_ID: Final = "b1a00492-073a-47ea-816f-4c329264a828"

# Helm/Vera pin (subset of grok-build default_oauth2_scopes).
SCOPES: Final = (
    "openid profile email offline_access "
    "grok-cli:access api:access conversations:read conversations:write"
)
SCOPE_LIST: Final[tuple[str, ...]] = tuple(SCOPES.split())

DEVICE_GRANT_TYPE: Final = "urn:ietf:params:oauth:grant-type:device_code"
REFRESH_GRANT_TYPE: Final = "refresh_token"
REFERRER: Final = "grok-build"
CODE_CHALLENGE_METHOD: Final = "S256"

DEFAULT_DEVICE_POLL_INTERVAL: Final = 5
SLOW_DOWN_INCREMENT: Final = 5
DEFAULT_EXPIRES_IN: Final = 3600

AUTH_METHOD_OAUTH: Final = "oauth"
AUTH_METHOD_API_KEY: Final = "api_key"
AuthMethod = Literal["oauth", "api_key"]
AUTH_METHODS: Final[tuple[AuthMethod, ...]] = (AUTH_METHOD_OAUTH, AUTH_METHOD_API_KEY)

# Home Assistant config-entry keys owned by this library's TokenSet.
ENTRY_KEY_ACCESS_TOKEN: Final = "access_token"
ENTRY_KEY_REFRESH_TOKEN: Final = "refresh_token"
ENTRY_KEY_EXPIRES_AT: Final = "expires_at"
ENTRY_KEY_TOKEN_TYPE: Final = "token_type"
ENTRY_KEY_SCOPE: Final = "scope"
ENTRY_KEY_AUTH_METHOD: Final = "auth_method"
ENTRY_KEY_API_KEY: Final = "api_key"

TOKEN_ENTRY_KEYS: Final[tuple[str, ...]] = (
    ENTRY_KEY_ACCESS_TOKEN,
    ENTRY_KEY_REFRESH_TOKEN,
    ENTRY_KEY_EXPIRES_AT,
    ENTRY_KEY_TOKEN_TYPE,
    ENTRY_KEY_SCOPE,
)
