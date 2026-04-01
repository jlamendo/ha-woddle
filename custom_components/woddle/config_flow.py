"""Config flow for Woddle integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from pywoddle import WoddleAuth, WoddleAuthError, WoddleClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class WoddleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Woddle."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            auth = WoddleAuth(email=email, password=password)
            try:
                await auth.authenticate()

                client = WoddleClient(auth)
                babies = await client.fetch_babies()

                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()

                baby_names = [b.first_name for b in babies]
                title = (
                    f"Woddle ({', '.join(baby_names)})"
                    if baby_names
                    else f"Woddle ({email})"
                )

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )
            except WoddleAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            finally:
                await auth.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
