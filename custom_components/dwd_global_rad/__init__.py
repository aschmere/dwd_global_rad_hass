"""The DWD Global Radiation Forecasts and Data integration."""

# pylint: disable=W0511
from __future__ import annotations

import logging

import dwd_global_radiation as dgr

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import (
    ForecastUpdateCoordinator,
    LocationDataUpdateCoordinator,
    MeasurementUpdateCoordinator,
)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


# async def async_setup(hass, config):
# """Set up the DWD Global Radiation Forecasts and Data component."""
# Use the external library
# pylint: disable=unused-variable
# objGlobalRadiation = dgr.GlobalRadiation()
# Your setup code here
#   return True


async def update_listener(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DWD Global Radiation Forecasts and Data from a config entry."""

    _LOGGER.debug("Setup with data %s", entry.data)
    # entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})
    if "api_client" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["api_client"] = dgr.GlobalRadiation()

    api_client = hass.data[DOMAIN]["api_client"]
    latitude = entry.data["latitude"]
    longitude = entry.data["longitude"]
    name = entry.data["name"]

    if api_client.get_location_by_name(name) is None:
        api_client.add_location(name=name, latitude=latitude, longitude=longitude)

    # Initialize ForecastUpdateCoordinator
    if "forecast_coordinator" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["forecast_coordinator"] = ForecastUpdateCoordinator(
            hass, api_client
        )
        await hass.data[DOMAIN][
            "forecast_coordinator"
        ].async_config_entry_first_refresh()

    # Initialize MeasurementUpdateCoordinator
    if "measurement_coordinator" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["measurement_coordinator"] = MeasurementUpdateCoordinator(
            hass, api_client
        )
        await hass.data[DOMAIN][
            "measurement_coordinator"
        ].async_config_entry_first_refresh()

    # Initialize LocationDataUpdateCoordinator
    name = entry.data["name"]
    location_coordinator = LocationDataUpdateCoordinator(
        hass,
        hass.data[DOMAIN]["forecast_coordinator"],
        hass.data[DOMAIN]["measurement_coordinator"],
        name,
    )
    await location_coordinator.async_config_entry_first_refresh()

    # Store only the location_coordinator in the entry's data
    hass.data[DOMAIN][entry.entry_id] = {"location_coordinator": location_coordinator}

    # Perform the first data fetch for the new location immediately
    await hass.data[DOMAIN]["measurement_coordinator"].async_request_refresh()
    await hass.data[DOMAIN]["forecast_coordinator"].async_request_refresh()

    # Setup platforms (e.g., sensor)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        # Check if there are any remaining entries
        if not hass.config_entries.async_entries(DOMAIN):
            # Perform additional cleanup if this was the last entry
            if "coordinator" in hass.data[DOMAIN]:
                # Perform any cleanup for the coordinator if necessary
                coordinator = hass.data[DOMAIN]["coordinator"]
                await coordinator.async_shutdown()
                hass.data[DOMAIN].pop("coordinator")

            # Clean up the API client if no locations are left
            if "api_client" in hass.data[DOMAIN]:
                api_client = hass.data[DOMAIN]["api_client"]
                if not api_client.locations:
                    hass.data[DOMAIN].pop("api_client")

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry."""
    api_client = hass.data[DOMAIN]["api_client"]
    name = entry.data["name"]

    # Remove the location from the api_client
    api_client.remove_location(name)

    # Clean up the entry data
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Optionally, clean up the api_client if no locations are left
    if not api_client.locations:
        hass.data[DOMAIN].pop("api_client")
        # Check and remove forecast and measurement coordinators if they exist
        forecast_coordinator = hass.data[DOMAIN].get("forecast_coordinator")
        measurement_coordinator = hass.data[DOMAIN].get("measurement_coordinator")

        if forecast_coordinator:
            hass.data[DOMAIN].pop("forecast_coordinator")

        if measurement_coordinator:
            hass.data[DOMAIN].pop("measurement_coordinator")

        # If hass.data[DOMAIN] is now empty, remove it completely
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
