"""Freeze the public surface and prove every ``__all__`` name imports."""

from __future__ import annotations

import ha_spacexai_auth as pkg

# Frozen public API. Update this list in the same change that edits ``__all__``.
FROZEN_PUBLIC_API = [
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
    "ensure_fresh",
    "generate_pkce",
    "poll_device_token",
    "poll_token",
    "refresh_access_token",
    "request_device_code",
    "start_device_auth",
    "token_data_updates",
]


def test_package_import_smoke() -> None:
    import ha_spacexai_auth

    assert ha_spacexai_auth.__version__ == "0.1.0"


def test_all_is_frozen() -> None:
    assert list(pkg.__all__) == FROZEN_PUBLIC_API


def test_every_all_name_imports() -> None:
    namespace: dict[str, object] = {}
    exec("from ha_spacexai_auth import *", namespace)
    for name in pkg.__all__:
        assert hasattr(pkg, name), f"{name} missing on package"
        assert name in namespace, f"{name} missing from star-import"
        assert namespace[name] is getattr(pkg, name)
