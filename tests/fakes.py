"""Shared aiohttp-like session double for tests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class FakeResponse:
    def __init__(self, status: int, payload: Any) -> None:
        self.status = status
        self._payload = payload

    async def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    async def text(self) -> str:
        if isinstance(self._payload, Exception):
            return ""
        return str(self._payload)

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeSession:
    def __init__(self, responses: Sequence[tuple[int, Any]]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def post(
        self,
        url: str,
        *,
        data: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> FakeResponse:
        self.calls.append((url, dict(data or {}), dict(headers or {})))
        if not self._responses:
            raise AssertionError(f"unexpected POST {url}")
        status, payload = self._responses.pop(0)
        return FakeResponse(status, payload)
