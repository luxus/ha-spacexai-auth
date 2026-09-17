"""Session-agnostic form POST (aiohttp ClientSession or lookalike)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class HttpResponse(Protocol):
    """Minimal aiohttp-like response."""

    status: int

    async def json(self) -> Any: ...

    async def text(self) -> str: ...


class HttpSession(Protocol):
    """Minimal aiohttp-like session: ``session.post(...)``.

    aiohttp returns an async context manager; some test doubles return an
    awaitable response. Both shapes are accepted.
    """

    def post(
        self,
        url: str,
        *,
        data: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any: ...


async def _read_payload(resp: HttpResponse) -> Any:
    try:
        return await resp.json()
    except Exception:
        try:
            return await resp.text()
        except Exception:
            return None


async def post_form(
    session: HttpSession,
    url: str,
    data: Mapping[str, str],
    *,
    extra_headers: Mapping[str, str] | None = None,
) -> tuple[int, Any]:
    """POST ``application/x-www-form-urlencoded`` and return ``(status, payload)``.

    ``payload`` is parsed JSON when possible, otherwise the response text.
    """
    headers: dict[str, str] = {"Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    result = session.post(url, data=dict(data), headers=headers)
    if hasattr(result, "__aenter__"):
        async with result as resp:
            return resp.status, await _read_payload(resp)
    resp = await result
    return resp.status, await _read_payload(resp)
