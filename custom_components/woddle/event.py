"""Event platform for Woddle."""

from __future__ import annotations

import logging

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WoddleCoordinator
from .entity import WoddleBabyEntity

_LOGGER = logging.getLogger(__name__)

type WoddleConfigEntry = ConfigEntry[WoddleCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WoddleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WoddleCoordinator = entry.runtime_data

    entities: list[EventEntity] = []
    for baby in coordinator.babies:
        bid = baby.baby_id
        name = baby.first_name
        if not bid:
            continue
        entities.extend([
            WoddleDiaperEvent(coordinator, bid, name),
            WoddleFeedingEvent(coordinator, bid, name),
            WoddleWeightEvent(coordinator, bid, name),
        ])

    async_add_entities(entities)


class WoddleDiaperEvent(WoddleBabyEntity, EventEntity):
    _attr_event_types = ["pee", "poop", "mixed", "dry", "wet", "dirty", "unknown"]
    _attr_icon = "mdi:baby-face-outline"
    _attr_name = "Diaper change"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "diaper_event")
        self._last_seen: set[str] = set()

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self.coordinator.data:
            return
        for activity in self.coordinator.data.get("activities", {}).get(self._baby_id, []):
            if (
                activity.activity_type == "diaper"
                and activity.activity_id
                and activity.activity_id not in self._last_seen
            ):
                self._last_seen.add(activity.activity_id)
                event_type = activity.sub_type if activity.sub_type in self._attr_event_types else "unknown"
                self._trigger_event(event_type, {"timestamp": activity.log_time, "title": activity.title})
        self.async_write_ha_state()


class WoddleFeedingEvent(WoddleBabyEntity, EventEntity):
    _attr_event_types = ["breast", "bottle", "solid", "formula", "nursing", "unknown"]
    _attr_icon = "mdi:baby-bottle"
    _attr_name = "Feeding"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "feeding_event")
        self._last_seen: set[str] = set()

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self.coordinator.data:
            return
        for activity in self.coordinator.data.get("activities", {}).get(self._baby_id, []):
            if (
                activity.activity_type == "feeding"
                and activity.activity_id
                and activity.activity_id not in self._last_seen
            ):
                self._last_seen.add(activity.activity_id)
                event_type = activity.sub_type if activity.sub_type in self._attr_event_types else "unknown"
                self._trigger_event(event_type, {"timestamp": activity.log_time})
        self.async_write_ha_state()


class WoddleWeightEvent(WoddleBabyEntity, EventEntity):
    _attr_event_types = ["measured"]
    _attr_icon = "mdi:scale-baby"
    _attr_name = "Weight measurement"

    def __init__(self, coordinator: WoddleCoordinator, baby_id: str, baby_name: str) -> None:
        super().__init__(coordinator, baby_id, baby_name, "weight_event")
        self._last_seen: set[str] = set()

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self.coordinator.data:
            return
        for activity in self.coordinator.data.get("activities", {}).get(self._baby_id, []):
            if (
                activity.activity_type == "weight"
                and activity.activity_id
                and activity.activity_id not in self._last_seen
            ):
                self._last_seen.add(activity.activity_id)
                self._trigger_event("measured", {
                    "weight": activity.value,
                    "unit": activity.unit,
                    "title": activity.title,
                    "timestamp": activity.log_time,
                })
        self.async_write_ha_state()
