"""The DWD Global Radiation Forecasts and Data integration."""

# pylint: disable=W0511
from __future__ import annotations

import asyncio
import logging
import os

import aiohttp
import dwd_global_radiation as dgr

from homeassistant.components.hassio import async_get_addon_info, async_start_addon
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_client import DWDGlobalRadAPIClient
from .const import ADDON_SLUG, DOMAIN
from .coordinator import (
    ForecastUpdateCoordinator,
    LocationDataUpdateCoordinator,
    MeasurementUpdateCoordinator,
)
from .restapi import DWDGlobalRadRESTApi

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def get_addon_config(hass: HomeAssistant, addon_slug: str):
    """Fetch add-on configuration from Supervisor."""
    try:
        supervisor_token = os.getenv("SUPERVISOR_TOKEN")
        if not supervisor_token:
            _LOGGER.error("Supervisor token not found in environment variables")
            raise ConfigEntryNotReady(
                "Supervisor token not found in environment variables"
            )

        url = f"http://supervisor/addons/{addon_slug}/info"
        headers = {
            "Authorization": f"Bearer {supervisor_token}",
            "Content-Type": "application/json",
        }

        session = async_get_clientsession(hass)
        _LOGGER.debug(f"Requesting add-on info from URL: {url} with headers: {headers}")
        async with session.get(url, headers=headers) as response:
            response_text = await response.text()
            _LOGGER.debug(
                f"Received response status: {response.status}, body: {response_text}"
            )
            if response.status != 200:
                raise ConfigEntryNotReady(
                    f"Error fetching add-on config: {response.status} - {response_text}"
                )
            data = await response.json()
            return data["data"]
    except Exception as e:
        _LOGGER.error(f"Error fetching add-on configuration: {e}")
        raise ConfigEntryNotReady(f"Error fetching add-on configuration: {e}")


async def update_listener(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DWD Global Radiation Forecasts and Data from a config entry."""

    _LOGGER.debug("Setup with data %s", entry.data)
    # entry.async_on_unload(entry.add_update_listener(update_listener))

    use_addon = True

    if use_addon:
        addon_info = await get_addon_config(hass, ADDON_SLUG)
        if not addon_info:
            raise ConfigEntryNotReady("No configuration found for the add-on")

        hostname = addon_info.get("hostname")
        port_number = next(iter(addon_info.get("network", {}).values()), 5001)

        # Ensure the add-on is started
        await ensure_addon_started(hass, ADDON_SLUG)
    else:
        hostname = "homeassistant.local"
        port_number = "5001"

    hass.data.setdefault(DOMAIN, {})
    if "api_client" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["api_client"] = DWDGlobalRadAPIClient(
            hass, hostname, port_number
        )
    if "rest_api_setup" not in hass.data[DOMAIN]:
        hass.http.register_view(DWDGlobalRadRESTApi(hass))
        hass.data[DOMAIN]["rest_api_setup"] = True

    api_client = hass.data[DOMAIN]["api_client"]
    latitude = entry.data["latitude"]
    longitude = entry.data["longitude"]
    name = entry.data["name"]

    if not await wait_for_api_server(api_client):
        raise ConfigEntryNotReady("API server not available after multiple attempts")

    location = await api_client.get_location_by_name(name)
    if location is None:
        await api_client.add_location(name=name, latitude=latitude, longitude=longitude)

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
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def ensure_addon_started(
    hass: HomeAssistant, addon_slug: str, retries=10, delay=10
) -> None:
    """Ensure the add-on is started."""
    for attempt in range(retries):
        addon_info = await async_get_addon_info(hass, addon_slug)
        if addon_info["state"] == "started":
            _LOGGER.debug("Add-on %s is already started", addon_slug)
            return
        _LOGGER.debug("Starting add-on %s", addon_slug)
        try:
            await async_start_addon(hass, addon_slug)
            # Wait a bit before checking the status again
            await asyncio.sleep(delay)
        except Exception as e:
            _LOGGER.error(f"Error starting add-on {addon_slug}: {e}")
            if attempt < retries - 1:
                _LOGGER.debug("Retrying to start add-on %s", addon_slug)
                await asyncio.sleep(delay)
            else:
                raise ConfigEntryNotReady(f"Error starting add-on {addon_slug}: {e}")


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


async def wait_for_api_server(api_client, retries=5, delay=10):
    """Wait for the API server to be available."""
    for attempt in range(retries):
        try:
            await (
                api_client.get_status()
            )  # Assuming get_status is a method to check the API server status
            return True
        except Exception as e:
            _LOGGER.warning(
                f"API server not available, retrying in {delay} seconds... (Attempt {attempt+1}/{retries})"
            )
            await asyncio.sleep(delay)
    return False
