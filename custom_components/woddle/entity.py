"""Base entity for the Woddle integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WoddleCoordinator


class WoddleBabyEntity(CoordinatorEntity[WoddleCoordinator]):
    """Base entity for a Woddle baby."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WoddleCoordinator,
        baby_id: str,
        baby_name: str,
        key: str,
    ) -> None:
        """Initialize.

        Args:
            coordinator: The data update coordinator.
            baby_id: Unique baby ID from Woddle API.
            baby_name: Baby's first name.
            key: Entity key suffix for unique_id.
        """
        super().__init__(coordinator)
        self._baby_id = baby_id
        self._baby_name = baby_name
        self._attr_unique_id = f"woddle_{baby_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, baby_id)},
            name=f"Woddle - {baby_name}",
            manufacturer="Woddle Baby, Inc.",
            model="Smart Changing Pad",
        )


class WoddleDeviceEntity(CoordinatorEntity[WoddleCoordinator]):
    """Base entity for a Woddle physical device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WoddleCoordinator,
        device_id: str,
        device_name: str,
        firmware_version: str | None,
        key: str,
    ) -> None:
        """Initialize.

        Args:
            coordinator: The data update coordinator.
            device_id: Device serial number.
            device_name: Device display name.
            firmware_version: Current firmware version.
            key: Entity key suffix for unique_id.
        """
        super().__init__(coordinator)
        self._attr_unique_id = f"woddle_device_{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Woddle Baby, Inc.",
            model="Smart Changing Pad",
            sw_version=firmware_version,
            serial_number=device_id,
        )
