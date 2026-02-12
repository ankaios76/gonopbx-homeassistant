"""Sensor platform for GonoPBX."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GonoPBXCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GonoPBX sensors from a config entry."""
    coordinator: GonoPBXCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        GonoPBXActiveCalls(coordinator, entry),
        GonoPBXCallsToday(coordinator, entry),
        GonoPBXCallsMissedToday(coordinator, entry),
        GonoPBXVoicemailUnread(coordinator, entry),
    ]
    async_add_entities(entities)


class GonoPBXSensorBase(CoordinatorEntity[GonoPBXCoordinator], SensorEntity):
    """Base class for GonoPBX sensors."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry, key: str, name: str, unit: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"GonoPBX {name}"
        self._attr_native_unit_of_measurement = unit
        self._key = key


class GonoPBXActiveCalls(GonoPBXSensorBase):
    """Number of active calls."""

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "active_calls", "Active Calls", "calls")
        self._attr_icon = "mdi:phone-in-talk"

    @property
    def native_value(self) -> int:
        calls = self.coordinator.data.get("calls", {})
        return calls.get("count", 0)


class GonoPBXCallsToday(GonoPBXSensorBase):
    """Number of calls today."""

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "calls_today", "Calls Today", "calls")
        self._attr_icon = "mdi:phone-log"

    @property
    def native_value(self) -> int:
        stats = self.coordinator.data.get("cdr_stats", {})
        return stats.get("calls_today", 0)


class GonoPBXCallsMissedToday(GonoPBXSensorBase):
    """Number of missed calls (total)."""

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "calls_missed", "Missed Calls", "calls")
        self._attr_icon = "mdi:phone-missed"

    @property
    def native_value(self) -> int:
        stats = self.coordinator.data.get("cdr_stats", {})
        return stats.get("missed_calls", 0)


class GonoPBXVoicemailUnread(GonoPBXSensorBase):
    """Number of unread voicemail messages."""

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "voicemail_unread", "Voicemail Unread", "messages")
        self._attr_icon = "mdi:voicemail"

    @property
    def native_value(self) -> int:
        vm = self.coordinator.data.get("voicemail", {})
        return vm.get("unread", 0)
