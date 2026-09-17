"""TokenSet and Home Assistant config-entry (de)serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .const import (
    AUTH_METHOD_API_KEY,
    AUTH_METHOD_OAUTH,
    AUTH_METHODS,
    DEFAULT_EXPIRES_IN,
    ENTRY_KEY_ACCESS_TOKEN,
    ENTRY_KEY_API_KEY,
    ENTRY_KEY_AUTH_METHOD,
    ENTRY_KEY_EXPIRES_AT,
    ENTRY_KEY_REFRESH_TOKEN,
    ENTRY_KEY_SCOPE,
    ENTRY_KEY_TOKEN_TYPE,
    AuthMethod,
)
from .errors import SpaceXaiAuthError, SpaceXaiEntitlementError


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass
class TokenSet:
    """OAuth token payload stored by HA integrations.

    Fields map 1:1 onto config-entry keys of the same name. ``auth_method``
    and ``api_key`` live on the entry, not on TokenSet; use
    :meth:`to_entry_data` / :meth:`from_entry_data`.
    """

    access_token: str
    refresh_token: str | None
    expires_at: float
    token_type: str = "Bearer"
    scope: str | None = None

    def to_entry_data(
        self,
        *,
        auth_method: AuthMethod = AUTH_METHOD_OAUTH,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Serialize to the Helm/Vera HA config-entry contract.

        Keys: ``access_token``, ``refresh_token``, ``expires_at``,
        ``token_type``, ``scope``, ``auth_method`` ∈ {``oauth``, ``api_key``},
        optional ``api_key``.
        """
        if auth_method not in AUTH_METHODS:
            raise SpaceXaiAuthError(
                f"auth_method must be one of {AUTH_METHODS}, got {auth_method!r}"
            )
        data = token_data_updates(self)
        data[ENTRY_KEY_AUTH_METHOD] = auth_method
        if api_key is not None:
            data[ENTRY_KEY_API_KEY] = api_key
        return data

    @classmethod
    def from_entry_data(cls, data: Mapping[str, Any]) -> TokenSet:
        """Parse TokenSet fields from HA config-entry data.

        Ignores ``auth_method`` / ``api_key`` (those stay in the integration).
        """
        access_token = _optional_str(data.get(ENTRY_KEY_ACCESS_TOKEN))
        if access_token is None:
            raise SpaceXaiAuthError("config entry is missing access_token")
        expires_at = data.get(ENTRY_KEY_EXPIRES_AT)
        if expires_at is None:
            raise SpaceXaiAuthError("config entry is missing expires_at")
        try:
            expires_at_ts = float(expires_at)
        except (TypeError, ValueError) as exc:
            raise SpaceXaiAuthError("config entry expires_at is not a number") from exc
        token_type = _optional_str(data.get(ENTRY_KEY_TOKEN_TYPE)) or "Bearer"
        return cls(
            access_token=access_token,
            refresh_token=_optional_str(data.get(ENTRY_KEY_REFRESH_TOKEN)),
            expires_at=expires_at_ts,
            token_type=token_type,
            scope=_optional_str(data.get(ENTRY_KEY_SCOPE)),
        )

    @classmethod
    def from_token_response(
        cls,
        payload: Mapping[str, Any],
        *,
        previous_refresh_token: str | None = None,
        now: float,
    ) -> TokenSet:
        """Parse an RFC 6749 token endpoint JSON body."""
        access_token = _optional_str(payload.get("access_token"))
        if access_token is None:
            raise SpaceXaiAuthError("token response is missing access_token")
        expires_in = payload.get("expires_in", DEFAULT_EXPIRES_IN)
        try:
            expires_in_s = int(expires_in)
        except (TypeError, ValueError) as exc:
            raise SpaceXaiAuthError("token response expires_in is not an integer") from exc
        refresh_token = _optional_str(payload.get("refresh_token"))
        if refresh_token is None:
            refresh_token = previous_refresh_token
        token_type = _optional_str(payload.get("token_type")) or "Bearer"
        return cls(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + expires_in_s,
            token_type=token_type,
            scope=_optional_str(payload.get("scope")),
        )

    def require_entitlement(self, scope: str = "grok-cli:access") -> None:
        """Raise if ``scope`` is advertised on the token but missing.

        When the IdP omits ``scope`` entirely, this is a no-op.
        """
        if self.scope is None:
            return
        granted = set(self.scope.split())
        if scope not in granted:
            raise SpaceXaiEntitlementError(
                f"token is missing required scope {scope!r}",
                error="insufficient_scope",
            )


def token_data_updates(tokens: TokenSet) -> dict[str, Any]:
    """Token-only dict for merging into an existing HA config entry.

    Does not include ``auth_method`` or ``api_key`` so a refresh cannot
    clobber the integration's chosen auth path.
    """
    return {
        ENTRY_KEY_ACCESS_TOKEN: tokens.access_token,
        ENTRY_KEY_REFRESH_TOKEN: tokens.refresh_token,
        ENTRY_KEY_EXPIRES_AT: tokens.expires_at,
        ENTRY_KEY_TOKEN_TYPE: tokens.token_type,
        ENTRY_KEY_SCOPE: tokens.scope,
    }
