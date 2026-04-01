"""Constants for the Woddle integration."""

DOMAIN = "woddle"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Polling interval (seconds)
DEFAULT_SCAN_INTERVAL = 120

# Platforms to set up
PLATFORMS = ["sensor", "event"]

# Event types fired to HA event bus
EVENT_DIAPER_CHANGE = f"{DOMAIN}_diaper_change"
EVENT_WEIGHT_MEASUREMENT = f"{DOMAIN}_weight_measurement"
EVENT_FEEDING = f"{DOMAIN}_feeding"
