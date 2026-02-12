"""Config flow for GonoPBX integration."""

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GonoPBXApiClient
from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_USE_MQTT, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_USE_MQTT, default=False): bool,
    }
)


class GonoPBXConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GonoPBX."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Prevent duplicate entries
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            # Validate connection
            session = async_get_clientsession(self.hass)
            client = GonoPBXApiClient(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_API_KEY],
                session,
            )

            try:
                if await client.async_check_connection():
                    return self.async_create_entry(
                        title=f"GonoPBX ({user_input[CONF_HOST]})",
                        data=user_input,
                    )
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
