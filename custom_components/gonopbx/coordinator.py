"""DataUpdateCoordinator for GonoPBX."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GonoPBXApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class GonoPBXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to poll GonoPBX REST API."""

    def __init__(self, hass: HomeAssistant, client: GonoPBXApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from GonoPBX API."""
        try:
            dashboard = await self.client.async_get_dashboard_status()
            calls = await self.client.async_get_active_calls()

            # CDR stats and voicemail are optional — don't fail if endpoint missing
            try:
                cdr_stats = await self.client.async_get_cdr_stats()
            except Exception:
                cdr_stats = {}

            try:
                voicemail = await self.client.async_get_voicemail_stats()
            except Exception:
                voicemail = {}

            return {
                "dashboard": dashboard,
                "calls": calls,
                "cdr_stats": cdr_stats,
                "voicemail": voicemail,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with GonoPBX: {err}") from err
