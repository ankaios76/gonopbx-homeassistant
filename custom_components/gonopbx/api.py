"""REST API client for GonoPBX."""

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class GonoPBXApiClient:
    """API client to communicate with GonoPBX backend."""

    def __init__(self, host: str, port: int, api_key: str, session: aiohttp.ClientSession) -> None:
        self._base_url = f"http://{host}:{port}"
        self._headers = {"X-API-Key": api_key}
        self._session = session

    async def _get(self, path: str) -> dict[str, Any]:
        """Make a GET request."""
        async with self._session.get(
            f"{self._base_url}{path}", headers=self._headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request."""
        async with self._session.post(
            f"{self._base_url}{path}", headers=self._headers, json=data
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _put(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a PUT request."""
        async with self._session.put(
            f"{self._base_url}{path}", headers=self._headers, json=data
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def async_check_connection(self) -> bool:
        """Test connection to GonoPBX."""
        try:
            result = await self._get("/api/health")
            return result.get("status") == "healthy"
        except Exception:
            return False

    async def async_get_dashboard_status(self) -> dict[str, Any]:
        """Get dashboard status (peers, trunks, system info)."""
        return await self._get("/api/dashboard/status")

    async def async_get_active_calls(self) -> dict[str, Any]:
        """Get currently active calls."""
        return await self._get("/api/calls/active")

    async def async_get_cdr_stats(self) -> dict[str, Any]:
        """Get call detail record statistics."""
        return await self._get("/api/cdr/stats")

    async def async_get_voicemail_stats(self) -> dict[str, Any]:
        """Get voicemail statistics."""
        return await self._get("/api/voicemail/stats")

    async def async_originate_call(self, extension: str, number: str) -> dict[str, Any]:
        """Originate a call."""
        return await self._post("/api/calls/originate", {"extension": extension, "number": number})

    async def async_toggle_forwarding(self, forward_id: int, enabled: bool, forward_type: str | None = None) -> dict[str, Any]:
        """Toggle call forwarding."""
        data: dict[str, Any] = {"enabled": enabled}
        if forward_type is not None:
            data["type"] = forward_type
        return await self._put(f"/api/callforward/{forward_id}", data)
