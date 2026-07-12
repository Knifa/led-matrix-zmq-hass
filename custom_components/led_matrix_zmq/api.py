from __future__ import annotations

from typing import Any

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=5)


class LmzApiError(Exception):
    """Raised when the server is unreachable or returns an error."""


class LmzApi:
    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self._session = session
        self._url = url.rstrip("/")

    async def _get(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(
                f"{self._url}{path}", timeout=TIMEOUT
            ) as res:
                res.raise_for_status()
                return await res.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise LmzApiError(f"GET {path} failed: {err}") from err

    async def _post(self, path: str, payload: dict[str, Any]) -> None:
        try:
            async with self._session.post(
                f"{self._url}{path}", json=payload, timeout=TIMEOUT
            ) as res:
                res.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise LmzApiError(f"POST {path} failed: {err}") from err

    async def _get_field(self, path: str, field: str) -> int:
        data = await self._get(path)
        try:
            return data[field]
        except (KeyError, TypeError) as err:
            raise LmzApiError(f"GET {path} returned unexpected payload") from err

    async def get_brightness(self) -> int:
        return await self._get_field("/brightness", "brightness")

    async def set_brightness(self, brightness: int, transition: int = 0) -> None:
        await self._post(
            "/brightness", {"brightness": brightness, "transition": transition}
        )

    async def get_temperature(self) -> int:
        return await self._get_field("/temperature", "temperature")

    async def set_temperature(self, temperature: int, transition: int = 0) -> None:
        await self._post(
            "/temperature", {"temperature": temperature, "transition": transition}
        )

    async def is_healthy(self) -> bool:
        try:
            async with self._session.get(
                f"{self._url}/healthcheck", timeout=TIMEOUT
            ) as res:
                res.raise_for_status()
        except (aiohttp.ClientError, TimeoutError):
            return False
        return True
