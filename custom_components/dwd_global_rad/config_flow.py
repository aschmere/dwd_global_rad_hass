"""Config flow for DWD Global Radiation Forecasts and Data integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DWD_GLOBAL_RAD_LATITUDE = vol.All(
    cv.latitude,  # Use the original cv.latitude validator
    vol.Range(min=46, max=57),  # Restrict latitude to a range covered by DWD data.
    vol.Coerce(float),
)

DWD_GLOBAL_RAD_LONGITUDE = vol.All(
    cv.longitude,  # Use the original cv.longitude validator
    vol.Range(min=5, max=16),  # Restrict longitude to a range covered by DWD data.
    vol.Coerce(float),
)


def get_user_data_schema(hass):
    """Return user data schema with default values from Home Assistant config."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=hass.config.location_name): str,
            vol.Required(
                CONF_LATITUDE, default=hass.config.latitude
            ): DWD_GLOBAL_RAD_LATITUDE,
            vol.Required(
                CONF_LONGITUDE, default=hass.config.longitude
            ): DWD_GLOBAL_RAD_LONGITUDE,
        }
    )


class DWDGlobalRadConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DWD Global Radiation Forecasts and Data."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for uniqueness of CONF_NAME
            if any(
                entry.data[CONF_NAME] == name for entry in self._async_current_entries()
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                await self.async_set_unique_id(name)
                self._abort_if_unique_id_configured()

                # Add location entry
                user_input["category"] = "location"
                return self.async_create_entry(title=name, data=user_input)

        user_input = user_input or {
            CONF_NAME: self.hass.config.location_name,
            CONF_LATITUDE: self.hass.config.latitude,
            CONF_LONGITUDE: self.hass.config.longitude,
        }

        # Display the form with default values and validation schema
        return self.async_show_form(
            step_id="user", data_schema=get_user_data_schema(self.hass), errors=errors
        )

    async def async_step_implicit_config_entry_create(
        self, data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle the implicit creation of a config entry."""
        return self.async_create_entry(title=data["name"], data=data)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
