"""Binary sensor platform for GonoPBX."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    """Set up GonoPBX binary sensors from a config entry."""
    coordinator: GonoPBXCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = []

    # System connectivity sensor
    entities.append(GonoPBXSystemSensor(coordinator, entry))

    # Extension and trunk sensors from endpoints list
    dashboard = coordinator.data.get("dashboard", {})
    for ep in dashboard.get("endpoints", []):
        ep_name = ep.get("endpoint", "")
        ep_type = ep.get("type", "peer")
        display_name = ep.get("display_name", ep_name)
        if not ep_name:
            continue
        if ep_type == "trunk":
            entities.append(GonoPBXTrunkSensor(coordinator, entry, ep_name, display_name))
        else:
            entities.append(GonoPBXExtensionSensor(coordinator, entry, ep_name, display_name))

    async_add_entities(entities)


class GonoPBXSystemSensor(CoordinatorEntity[GonoPBXCoordinator], BinarySensorEntity):
    """Binary sensor for GonoPBX system connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_system"
        self._attr_name = "GonoPBX System"
        self._attr_icon = "mdi:server-network"

    @property
    def is_on(self) -> bool:
        dashboard = self.coordinator.data.get("dashboard", {})
        return dashboard.get("asterisk") == "connected"


class GonoPBXExtensionSensor(CoordinatorEntity[GonoPBXCoordinator], BinarySensorEntity):
    """Binary sensor for a SIP extension."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry, endpoint: str, display_name: str) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._attr_unique_id = f"{entry.entry_id}_ext_{endpoint}"
        self._attr_name = f"GonoPBX Ext {display_name}"
        self._attr_icon = "mdi:phone-voip"

    @property
    def is_on(self) -> bool:
        dashboard = self.coordinator.data.get("dashboard", {})
        for ep in dashboard.get("endpoints", []):
            if ep.get("endpoint") == self._endpoint:
                return ep.get("status") == "online"
        return False


class GonoPBXTrunkSensor(CoordinatorEntity[GonoPBXCoordinator], BinarySensorEntity):
    """Binary sensor for a SIP trunk."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: GonoPBXCoordinator, entry: ConfigEntry, endpoint: str, display_name: str) -> None:
        super().__init__(coordinator)
        self._endpoint = endpoint
        self._attr_unique_id = f"{entry.entry_id}_trunk_{endpoint}"
        self._attr_name = f"GonoPBX Trunk {display_name}"
        self._attr_icon = "mdi:phone-classic"

    @property
    def is_on(self) -> bool:
        dashboard = self.coordinator.data.get("dashboard", {})
        for ep in dashboard.get("endpoints", []):
            if ep.get("endpoint") == self._endpoint:
                return ep.get("status") == "online"
        return False
