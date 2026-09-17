# ha-spacexai-auth

Shared **SpaceXAI / xAI Grok OAuth helpers** for Home Assistant integrations
(device code, PKCE S256, refresh, `TokenSet`).

This is **Phase A only**: a pure Python library. There is **no** Home Assistant
domain, Config Flow UI, TTS, Jev router, or Application Credentials in this
repo. Those stay in each integration.

## Install

```bash
pip install ha-spacexai-auth
```

Until this is on PyPI, integrations can depend on a git pin:

```
ha-spacexai-auth @ git+https://github.com/luxus/ha-spacexai-auth.git@main
```

Home Assistant `manifest.json`:

```json
{
  "requirements": ["ha-spacexai-auth==0.1.0"]
}
```

Requires **Python ≥ 3.11**. No Home Assistant dependency. HTTP is
session-agnostic: pass any **aiohttp-like** object with `.post(...)`
(Home Assistant’s `async_get_clientsession(hass)` works).

## How jev / TTS will import

```python
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
    poll_device_token,   # alias of poll_token
    poll_token,
    refresh_access_token,
    request_device_code,  # alias of start_device_auth
    start_device_auth,
    token_data_updates,
)

# Config Flow lives in the integration, not here:
session = async_get_clientsession(hass)
device = await start_device_auth(session)
# Show device.user_code + device.verification_uri_complete to the user.
tokens = await poll_token(session, device)
hass.config_entries.async_update_entry(entry, data=tokens.to_entry_data())

# API calls:
headers = authorization_headers(tokens.access_token)

# On expiry, merge token keys only (auth_method / api_key stay put):
tokens = await refresh_access_token(session, tokens)
hass.config_entries.async_update_entry(
    entry, data={**entry.data, **token_data_updates(tokens)}
)
```

Package import path: **`ha_spacexai_auth`**.

## Public API

| Symbol | Role |
| --- | --- |
| `generate_pkce` | RFC 7636 S256 `PkcePair` |
| `start_device_auth` / `request_device_code` | RFC 8628 device-code start |
| `poll_token` / `poll_device_token` | Poll until token, `slow_down`, or expiry |
| `refresh_access_token` | `grant_type=refresh_token`; keep old RT if omitted |
| `TokenSet` | `access_token`, `refresh_token`, `expires_at`, `token_type`, `scope` |
| `TokenSet.to_entry_data` / `from_entry_data` | HA config-entry roundtrip |
| `token_data_updates` | Token keys only (no `auth_method` / `api_key`) |
| `authorization_headers` | `Authorization: Bearer …` |
| `DeviceAuthorization`, `PkcePair` | Device-flow types |
| `SpaceXaiAuthError`, `SpaceXaiAuthExpired`, `SpaceXaiEntitlementError` | Typed errors (`error` code optional) |
| Constants | `ISSUER`, `CLIENT_ID`, URLs, `SCOPES`, `DEVICE_GRANT_TYPE`, `REFERRER`, … |

### Modules

| Module | Contents |
| --- | --- |
| `ha_spacexai_auth.const` | Issuer, discovery, device/token/revoke URLs, public client, scopes |
| `ha_spacexai_auth.device_flow` | `start_device_auth` / `poll_token` (RFC 8628 + PKCE S256) |
| `ha_spacexai_auth.refresh` | Refresh; persist rotated refresh token |
| `ha_spacexai_auth.store` | `TokenSet`, `to_entry_data` / `from_entry_data` |
| `ha_spacexai_auth.headers` | Bearer `Authorization` |
| `ha_spacexai_auth.errors` | `SpaceXaiAuthError`, `SpaceXaiAuthExpired`, `SpaceXaiEntitlementError` |

## Config entry contract

`TokenSet.to_entry_data()` / `from_entry_data()` use these keys:

| Key | Notes |
| --- | --- |
| `access_token` | required |
| `refresh_token` | optional (`None` if the IdP did not issue one) |
| `expires_at` | Unix timestamp (float) |
| `token_type` | default `Bearer` |
| `scope` | space-delimited; optional |
| `auth_method` | `oauth` or `api_key` (on the entry, not on `TokenSet`) |
| `api_key` | optional; integrations keep this, not the library core |

## Pinned OAuth constants

Verified against
[`xai-org/grok-build` `crates/codegen/xai-grok-login/src/config.rs`](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-login/src/config.rs)
and discovery at `https://auth.x.ai/.well-known/openid-configuration`.

| Constant | Value |
| --- | --- |
| Issuer | `https://auth.x.ai` |
| Client ID | `b1a00492-073a-47ea-816f-4c329264a828` (public, **no secret**) |
| Device | `https://auth.x.ai/oauth2/device/code` |
| Token | `https://auth.x.ai/oauth2/token` |
| Revoke | `https://auth.x.ai/oauth2/revoke` |
| Grant | `urn:ietf:params:oauth:grant-type:device_code` |
| Referrer | `grok-build` |
| Scopes | `openid profile email offline_access grok-cli:access api:access conversations:read conversations:write` |

Helm/Vera pins the eight-scope set above (same as luxus/pi-xai). grok-build
`default_oauth2_scopes()` also currently lists `workspaces:read` and
`workspaces:write`; those are not requested here.

## Phase B (out of scope)

Shared Home Assistant config-entry helpers / a reusable Config Flow live in
each integration (jev, TTS, …), not in this package.

## License

MIT
