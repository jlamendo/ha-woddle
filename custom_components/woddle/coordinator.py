"""DataUpdateCoordinator for Woddle."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from pywoddle import (
    WoddleActivity,
    WoddleApiError,
    WoddleBaby,
    WoddleClient,
    WoddleDashboard,
    WoddleDevice,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_DIAPER_CHANGE,
    EVENT_FEEDING,
    EVENT_WEIGHT_MEASUREMENT,
)

_LOGGER = logging.getLogger(__name__)


class WoddleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Woddle data."""

    def __init__(self, hass: HomeAssistant, client: WoddleClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.babies: list[WoddleBaby] = []
        self.devices: list[WoddleDevice] = []
        self.dashboards: dict[str, WoddleDashboard] = {}
        self._seen_activity_ids: set[str] = set()
        self._first_update = True

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if not self.babies:
                self.babies = await self.client.fetch_babies()
                _LOGGER.debug("Found %d babies", len(self.babies))

            if not self.devices:
                try:
                    self.devices = await self.client.fetch_devices()
                except WoddleApiError:
                    _LOGGER.debug("Could not fetch devices")

            all_activities: dict[str, list[WoddleActivity]] = {}

            for baby in self.babies:
                bid = baby.baby_id
                if not bid:
                    continue

                # Fetch dashboard (has activity_type_ids and latest per type)
                try:
                    self.dashboards[bid] = await self.client.fetch_dashboard(bid)
                except WoddleApiError as err:
                    _LOGGER.debug("Dashboard fetch failed for %s: %s", bid, err)

                # Fetch today's calendar (full activity details with values)
                try:
                    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    activities = await self.client.fetch_calendar(bid, date=today)
                    all_activities[bid] = activities
                    self._process_new_activities(baby, activities)
                except WoddleApiError as err:
                    _LOGGER.debug("Calendar fetch failed for %s: %s", bid, err)
                    all_activities[bid] = []

            return {
                "babies": self.babies,
                "devices": self.devices,
                "dashboards": self.dashboards,
                "activities": all_activities,
            }

        except WoddleApiError as err:
            raise UpdateFailed(f"Error communicating with Woddle API: {err}") from err

    def _process_new_activities(
        self, baby: WoddleBaby, activities: list[WoddleActivity]
    ) -> None:
        for activity in activities:
            if not activity.activity_id or activity.activity_id in self._seen_activity_ids:
                continue

            self._seen_activity_ids.add(activity.activity_id)

            if self._first_update:
                continue

            event_data = {
                "baby_name": baby.first_name,
                "activity_id": activity.activity_id,
                "activity_type": activity.activity_type,
                "type": activity.sub_type,
                "timestamp": activity.log_time,
            }

            if activity.activity_type == "diaper":
                event_data["diaper_type"] = activity.sub_type
                self.hass.bus.async_fire(EVENT_DIAPER_CHANGE, event_data)

            elif activity.activity_type == "weight":
                event_data["weight"] = activity.value
                event_data["unit"] = activity.unit
                event_data["title"] = activity.title
                self.hass.bus.async_fire(EVENT_WEIGHT_MEASUREMENT, event_data)

            elif activity.activity_type == "feeding":
                event_data["feeding_type"] = activity.sub_type
                self.hass.bus.async_fire(EVENT_FEEDING, event_data)

        self._first_update = False
