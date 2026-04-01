"""The Woddle Smart Baby Scale integration."""

from __future__ import annotations

import logging

from pywoddle import WoddleAuth, WoddleAuthError, WoddleClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import CONF_EMAIL, CONF_PASSWORD, PLATFORMS
from .coordinator import WoddleCoordinator

_LOGGER = logging.getLogger(__name__)

type WoddleConfigEntry = ConfigEntry[WoddleCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WoddleConfigEntry) -> bool:
    """Set up Woddle from a config entry."""
    auth = WoddleAuth(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await auth.authenticate()
    except WoddleAuthError as err:
        await auth.close()
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except Exception as err:
        await auth.close()
        raise ConfigEntryNotReady(f"Could not connect to Woddle: {err}") from err

    client = WoddleClient(auth)
    coordinator = WoddleCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WoddleConfigEntry
) -> bool:
    """Unload a Woddle config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: WoddleCoordinator = entry.runtime_data
        await coordinator.client.close()
    return unloaded
