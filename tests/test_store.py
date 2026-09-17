from __future__ import annotations

import pytest

from ha_spacexai_auth import (
    AUTH_METHOD_API_KEY,
    AUTH_METHOD_OAUTH,
    SpaceXaiAuthError,
    SpaceXaiEntitlementError,
    TokenSet,
    authorization_headers,
    token_data_updates,
)


def _sample_tokens() -> TokenSet:
    return TokenSet(
        access_token="at-1",
        refresh_token="rt-1",
        expires_at=1_700_000_000.0,
        token_type="Bearer",
        scope="openid profile",
    )


def test_tokenset_roundtrip_oauth() -> None:
    tokens = _sample_tokens()
    entry = tokens.to_entry_data()
    assert entry == {
        "access_token": "at-1",
        "refresh_token": "rt-1",
        "expires_at": 1_700_000_000.0,
        "token_type": "Bearer",
        "scope": "openid profile",
        "auth_method": AUTH_METHOD_OAUTH,
    }
    restored = TokenSet.from_entry_data(entry)
    assert restored == tokens
    # Extra HA keys must be ignored on parse.
    restored2 = TokenSet.from_entry_data({**entry, "api_key": "sk-live", "extra": 1})
    assert restored2 == tokens


def test_tokenset_roundtrip_api_key_entry() -> None:
    tokens = _sample_tokens()
    entry = tokens.to_entry_data(auth_method=AUTH_METHOD_API_KEY, api_key="sk-live")
    assert entry["auth_method"] == "api_key"
    assert entry["api_key"] == "sk-live"
    restored = TokenSet.from_entry_data(entry)
    assert restored.access_token == "at-1"
    assert "api_key" not in token_data_updates(restored)
    assert "auth_method" not in token_data_updates(restored)


def test_token_data_updates_does_not_touch_auth_method() -> None:
    updates = token_data_updates(_sample_tokens())
    assert set(updates) == {
        "access_token",
        "refresh_token",
        "expires_at",
        "token_type",
        "scope",
    }


def test_from_entry_data_missing_access_token() -> None:
    with pytest.raises(SpaceXaiAuthError, match="access_token"):
        TokenSet.from_entry_data({"expires_at": 1.0})


def test_from_entry_data_missing_expires_at() -> None:
    with pytest.raises(SpaceXaiAuthError, match="expires_at"):
        TokenSet.from_entry_data({"access_token": "at"})


def test_to_entry_data_rejects_unknown_auth_method() -> None:
    with pytest.raises(SpaceXaiAuthError, match="auth_method"):
        _sample_tokens().to_entry_data(auth_method="password")  # type: ignore[arg-type]


def test_from_token_response_keeps_previous_refresh_token() -> None:
    tokens = TokenSet.from_token_response(
        {"access_token": "new-at", "expires_in": 60, "token_type": "Bearer"},
        previous_refresh_token="old-rt",
        now=1_000.0,
    )
    assert tokens.access_token == "new-at"
    assert tokens.refresh_token == "old-rt"
    assert tokens.expires_at == 1_060.0


def test_from_token_response_rotates_refresh_token() -> None:
    tokens = TokenSet.from_token_response(
        {
            "access_token": "new-at",
            "refresh_token": "new-rt",
            "expires_in": 120,
            "scope": "openid",
        },
        previous_refresh_token="old-rt",
        now=0.0,
    )
    assert tokens.refresh_token == "new-rt"
    assert tokens.scope == "openid"


def test_authorization_headers() -> None:
    assert authorization_headers("abc") == {"Authorization": "Bearer abc"}


def test_require_entitlement() -> None:
    tokens = _sample_tokens()
    tokens.require_entitlement("openid")
    with pytest.raises(SpaceXaiEntitlementError) as exc:
        tokens.require_entitlement("grok-cli:access")
    assert exc.value.error == "insufficient_scope"
    TokenSet(
        access_token="at",
        refresh_token=None,
        expires_at=1.0,
        scope=None,
    ).require_entitlement("grok-cli:access")
