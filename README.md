# Woddle Smart Baby Scale for Home Assistant

Home Assistant integration for the [Woddle Smart Changing Pad](https://www.woddlebaby.com/) using the unofficial API.

> **Note:** This uses an unofficial API. Woddle may change or restrict access at any time.

## Features

| Entity | Type | Description |
|--------|------|-------------|
| Diaper changes today | Sensor | Daily count with wet/dirty/mixed breakdown |
| Last diaper change | Sensor | Timestamp of most recent change |
| Feedings today | Sensor | Daily count with breast/bottle breakdown |
| Last activity | Sensor | Most recent tracked activity |
| Diaper change | Event | Fires on new diaper changes |
| Feeding | Event | Fires on new feedings |

Also fires `woddle_diaper_change`, `woddle_feeding`, and `woddle_weight_measurement` events on the HA bus for use in automations.

## Installation

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jlamendo&repository=ha-woddle&category=integration)

Or manually: copy `custom_components/woddle` to your HA `config/custom_components/` directory.

## Setup

1. Restart Home Assistant
2. Go to **Settings → Devices & Services → Add Integration**
3. Search for **Woddle**
4. Enter your Woddle account email and password
