"""Sensor platform for Woddle."""

from __future__ import annotations

import logging
from datetime import datetime

from pywoddle import WoddleActivity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
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
    coordinator: WoddleCoordinator = entry.runtime_data

    entities: list[SensorEntity] = []
    for baby in coordinator.babies:
        bid = baby.baby_id
        name = baby.first_name
        if not bid:
            continue
        entities.extend([
            WoddleWeightSensor(coordinator, bid, name),
            WoddleDiaperCountSensor(coordinator, bid, name),
            WoddleLastDiaperSensor(coordinator, bid, name),
            WoddleFeedingCountSensor(coordinator, bid, name),
            WoddleLastActivitySensor(coordinator, bid, name),
        ])

    for device in coordinator.devices:
        entities.append(
            WoddleDeviceInfoSensor(
                coordinator, device.device_id, device.name, device.firmware_version,
            )
        )

    async_add_entities(entities)


def _get_activities(
    coordinator: WoddleCoordinator, baby_id: str, activity_type: str | None = None
) -> list[WoddleActivity]:
    if not coordinator.data:
        return []
    activities = coordinator.data.get("activities", {}).get(baby_id, [])
    if activity_type:
        return [a for a in activities if a.activity_type == activity_type]
    return activities


class WoddleWeightSensor(WoddleBabyEntity, SensorEntity):
    """Latest weight measurement."""

    _attr_native_unit_of_measurement = UnitOfMass.POUNDS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:scale-baby"
    _attr_name = "Weight"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "weight")

    @callback
    def _handle_coordinator_update(self) -> None:
        weights = _get_activities(self.coordinator, self._baby_id, "weight")
        if weights:
            latest = max(weights, key=lambda w: w.log_time)
            self._attr_native_value = latest.value
            self._attr_extra_state_attributes = {
                "unit": latest.unit,
                "title": latest.title,
                "is_birth_weight": latest.is_birth_weight,
                "timestamp": latest.log_time,
            }
        else:
            self._attr_native_value = None
        self.async_write_ha_state()


class WoddleDiaperCountSensor(WoddleBabyEntity, SensorEntity):
    """Today's diaper change count."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:baby-face-outline"
    _attr_name = "Diaper changes today"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "diaper_count")

    @callback
    def _handle_coordinator_update(self) -> None:
        diapers = _get_activities(self.coordinator, self._baby_id, "diaper")
        self._attr_native_value = len(diapers)
        self._attr_extra_state_attributes = {
            "wet": sum(1 for a in diapers if a.sub_type in ("pee", "wet")),
            "dirty": sum(1 for a in diapers if a.sub_type in ("poop", "dirty")),
            "mixed": sum(1 for a in diapers if a.sub_type in ("mixed", "both")),
        }
        self.async_write_ha_state()


class WoddleLastDiaperSensor(WoddleBabyEntity, SensorEntity):
    """Last diaper change time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    _attr_name = "Last diaper change"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "last_diaper")

    @callback
    def _handle_coordinator_update(self) -> None:
        diapers = _get_activities(self.coordinator, self._baby_id, "diaper")
        if diapers:
            latest = max(diapers, key=lambda d: d.log_time)
            try:
                self._attr_native_value = datetime.fromisoformat(
                    latest.log_time.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "type": latest.sub_type,
                "title": latest.title,
            }
        else:
            self._attr_native_value = None
        self.async_write_ha_state()


class WoddleFeedingCountSensor(WoddleBabyEntity, SensorEntity):
    """Today's feeding count."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:baby-bottle"
    _attr_name = "Feedings today"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "feeding_count")

    @callback
    def _handle_coordinator_update(self) -> None:
        feedings = _get_activities(self.coordinator, self._baby_id, "feeding")
        self._attr_native_value = len(feedings)
        self._attr_extra_state_attributes = {
            "breast": sum(1 for f in feedings if "nursing" in (f.sub_type or "")),
            "bottle": sum(1 for f in feedings if "bottle" in (f.sub_type or "")),
        }
        self.async_write_ha_state()


class WoddleLastActivitySensor(WoddleBabyEntity, SensorEntity):
    """Most recent activity of any type."""

    _attr_icon = "mdi:baby-carriage"
    _attr_name = "Last activity"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "last_activity")

    @callback
    def _handle_coordinator_update(self) -> None:
        all_acts = _get_activities(self.coordinator, self._baby_id)
        if all_acts:
            latest = max(all_acts, key=lambda a: a.log_time)
            self._attr_native_value = latest.title or (
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
    """Device info sensor."""

    _attr_icon = "mdi:scale-baby"
    _attr_name = None

    def __init__(
        self, coordinator: WoddleCoordinator, device_id: str,
        device_name: str, firmware_version: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, firmware_version, "info")
        self._attr_native_value = device_name
        self._attr_extra_state_attributes = {
            "firmware_version": firmware_version,
            "serial_number": device_id,
        }
