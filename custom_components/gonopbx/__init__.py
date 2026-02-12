"""GonoPBX integration for Home Assistant."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GonoPBXApiClient
from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_USE_MQTT, DOMAIN
from .coordinator import GonoPBXCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

SERVICE_MAKE_CALL_SCHEMA = vol.Schema(
    {
        vol.Required("extension"): str,
        vol.Required("number"): str,
    }
)

SERVICE_TOGGLE_FWD_SCHEMA = vol.Schema(
    {
        vol.Required("forward_id"): int,
        vol.Required("enabled"): bool,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GonoPBX from a config entry."""
    session = async_get_clientsession(hass)
    client = GonoPBXApiClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_API_KEY],
        session,
    )

    coordinator = GonoPBXCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Subscribe to MQTT topics if enabled
    if entry.data.get(CONF_USE_MQTT):
        await _async_setup_mqtt(hass, entry)

    # Register services (once for the domain)
    if not hass.services.has_service(DOMAIN, "make_call"):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register GonoPBX services."""

    async def handle_make_call(call: ServiceCall) -> None:
        """Handle make_call service."""
        for entry_data in hass.data[DOMAIN].values():
            client: GonoPBXApiClient = entry_data["client"]
            await client.async_originate_call(
                call.data["extension"], call.data["number"]
            )
            break  # use first configured instance

    async def handle_toggle_forwarding(call: ServiceCall) -> None:
        """Handle toggle_forwarding service."""
        for entry_data in hass.data[DOMAIN].values():
            client: GonoPBXApiClient = entry_data["client"]
            await client.async_toggle_forwarding(
                call.data["forward_id"], call.data["enabled"]
            )
            break

    hass.services.async_register(
        DOMAIN, "make_call", handle_make_call, schema=SERVICE_MAKE_CALL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "toggle_forwarding", handle_toggle_forwarding, schema=SERVICE_TOGGLE_FWD_SCHEMA
    )


async def _async_setup_mqtt(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Subscribe to GonoPBX MQTT topics and fire HA events."""
    try:
        from homeassistant.components.mqtt import async_subscribe
    except ImportError:
        _LOGGER.warning("MQTT integration not available — skipping MQTT subscriptions")
        return

    async def _mqtt_message_received(msg) -> None:
        """Handle incoming MQTT messages from GonoPBX."""
        topic = msg.topic
        try:
            import json
            payload = json.loads(msg.payload)
        except (ValueError, TypeError):
            payload = {"value": msg.payload}

        # Map topics to HA events
        if topic == "gonopbx/call/started":
            hass.bus.async_fire("gonopbx_call_started", payload)
        elif topic == "gonopbx/call/answered":
            hass.bus.async_fire("gonopbx_call_answered", payload)
        elif topic == "gonopbx/call/ended":
            hass.bus.async_fire("gonopbx_call_ended", payload)

    await async_subscribe(hass, "gonopbx/#", _mqtt_message_received, qos=1)
    _LOGGER.info("Subscribed to GonoPBX MQTT topics")
