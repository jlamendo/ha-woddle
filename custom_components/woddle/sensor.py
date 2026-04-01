"""Sensor platform for Woddle."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pywoddle import WoddleActivity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WoddleCoordinator
from .entity import WoddleBabyEntity, WoddleDeviceEntity

_LOGGER = logging.getLogger(__name__)

type WoddleConfigEntry = ConfigEntry[WoddleCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WoddleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Woddle sensors from a config entry."""
    coordinator: WoddleCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    for baby in coordinator.babies:
        entities.extend([
            WoddleDiaperCountSensor(coordinator, baby.baby_id, baby.first_name),
            WoddleLastDiaperSensor(coordinator, baby.baby_id, baby.first_name),
            WoddleFeedingCountSensor(coordinator, baby.baby_id, baby.first_name),
            WoddleLastActivitySensor(coordinator, baby.baby_id, baby.first_name),
        ])

    for device in coordinator.devices:
        entities.append(
            WoddleDeviceInfoSensor(
                coordinator,
                device.device_id,
                device.name,
                device.firmware_version,
            )
        )

    async_add_entities(entities)


def _filter_activities(
    activities: list[WoddleActivity], baby_name: str, activity_type: str
) -> list[WoddleActivity]:
    """Filter activities by baby name and type."""
    return [
        a
        for a in activities
        if a.baby_name == baby_name and a.activity_type == activity_type
    ]


class WoddleDiaperCountSensor(WoddleBabyEntity, SensorEntity):
    """Sensor for today's diaper change count."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:baby-face-outline"
    _attr_name = "Diaper changes today"

    def __init__(
        self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, baby_id, baby_name, "diaper_count")

    @callback
    def _handle_coordinator_update(self) -> None:
        activities = self.coordinator.data.get("activities", []) if self.coordinator.data else []
        diapers = _filter_activities(activities, self._baby_name, "diaper")
        self._attr_native_value = len(diapers)
        self._attr_extra_state_attributes = {
            "wet": sum(1 for a in diapers if a.sub_type in ("pee", "wet")),
            "dirty": sum(1 for a in diapers if a.sub_type in ("poop", "dirty")),
            "mixed": sum(1 for a in diapers if a.sub_type in ("mixed", "both")),
        }
        self.async_write_ha_state()


class WoddleLastDiaperSensor(WoddleBabyEntity, SensorEntity):
    """Sensor for last diaper change time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    _attr_name = "Last diaper change"

    def __init__(
        self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, baby_id, baby_name, "last_diaper")

    @callback
    def _handle_coordinator_update(self) -> None:
        activities = self.coordinator.data.get("activities", []) if self.coordinator.data else []
        diapers = _filter_activities(activities, self._baby_name, "diaper")
        if diapers:
            latest = max(diapers, key=lambda d: d.log_time)
            try:
                self._attr_native_value = datetime.fromisoformat(
                    latest.log_time.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                self._attr_native_value = None
            self._attr_extra_state_attributes = {"type": latest.sub_type}
        else:
            self._attr_native_value = None
        self.async_write_ha_state()


class WoddleFeedingCountSensor(WoddleBabyEntity, SensorEntity):
    """Sensor for today's feeding count."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:baby-bottle"
    _attr_name = "Feedings today"

    def __init__(
        self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, baby_id, baby_name, "feeding_count")

    @callback
    def _handle_coordinator_update(self) -> None:
        activities = self.coordinator.data.get("activities", []) if self.coordinator.data else []
        feedings = _filter_activities(activities, self._baby_name, "feeding")
        self._attr_native_value = len(feedings)
        self._attr_extra_state_attributes = {
            "breast": sum(1 for f in feedings if "breast" in f.sub_type),
            "bottle": sum(1 for f in feedings if "bottle" in f.sub_type),
        }
        self.async_write_ha_state()


class WoddleLastActivitySensor(WoddleBabyEntity, SensorEntity):
    """Sensor showing the last activity of any type."""

    _attr_icon = "mdi:baby-carriage"
    _attr_name = "Last activity"

    def __init__(
        self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, baby_id, baby_name, "last_activity")

    @callback
    def _handle_coordinator_update(self) -> None:
        activities = self.coordinator.data.get("activities", []) if self.coordinator.data else []
        mine = [a for a in activities if a.baby_name == self._baby_name]
        if mine:
            latest = max(mine, key=lambda a: a.log_time)
            self._attr_native_value = (
                f"{latest.activity_type} ({latest.sub_type})"
                if latest.sub_type
                else latest.activity_type
            )
            self._attr_extra_state_attributes = {
                "activity_type": latest.activity_type,
                "type": latest.sub_type,
                "timestamp": latest.log_time,
            }
        else:
            self._attr_native_value = None
        self.async_write_ha_state()


class WoddleDeviceInfoSensor(WoddleDeviceEntity, SensorEntity):
    """Sensor for Woddle device status."""

    _attr_icon = "mdi:scale-baby"
    _attr_name = None  # Primary feature of device

    def __init__(
        self,
        coordinator: WoddleCoordinator,
        device_id: str,
        device_name: str,
        firmware_version: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator, device_id, device_name, firmware_version, "info")
        self._attr_native_value = device_name
        self._attr_extra_state_attributes = {
            "firmware_version": firmware_version,
            "serial_number": device_id,
        }
