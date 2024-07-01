"""Coordinator module for DWD Global Radiation integration in Home Assistant.

This module defines the update coordinators responsible for fetching and coordinating data updates
for global radiation measurements and forecasts from the DWD Open Data Servers.

Classes:
    ForecastUpdateCoordinator: Handles updates for forecast data.
    MeasurementUpdateCoordinator: Handles updates for measurement data.
    LocationDataUpdateCoordinator: Coordinates updates for a specific location, combining forecast
    and measurement data.

Usage:
    This module should be used within the DWD Global Radiation integration to manage data fetching
    and synchronization for various locations and sensor types.

Classes:
    ForecastUpdateCoordinator: Fetches and updates forecast data from the DWD API.
    MeasurementUpdateCoordinator: Fetches and updates measurement data from the DWD API.
    LocationDataUpdateCoordinator: Combines forecast and measurement data for a specific location
    and provides it to registered listeners.

Methods (ForecastUpdateCoordinator):
    __init__: Initialize the coordinator with the given Home Assistant instance and API client.
    _async_update_data: Fetch new forecast data from the DWD API.

Methods (MeasurementUpdateCoordinator):
    __init__: Initialize the coordinator with the given Home Assistant instance and API client.
    _async_update_data: Fetch new measurement data from the DWD API.

Methods (LocationDataUpdateCoordinator):
    __init__: Initialize the coordinator with the given Home Assistant instance, forecast
    coordinator, measurement coordinator, and location name.
    location_data: Extract data for the specific location using the unique name.
    _async_update_data: Fetch data for the specific location.
    _handle_update: Handle updates from child coordinators.
"""

import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientConnectorError, ServerDisconnectedError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DWDGlobalRadiationData:
    """Keep data for DWD Global Radiation entities."""


class ForecastUpdateCoordinator(DataUpdateCoordinator):
    """Handles periodic fetching and updating of forecast data from the DWD Open Data server.

    Methods:
    __init__: Initializes the coordinator with the given Home Assistant instance and API client.
    Sets the update interval to fetch forecasts every hour.
    _async_update_data: Fetches new forecast data from the DWD Open Data server.
    Updates listeners with the fetched data. Logs and raises
    an UpdateFailed exception if fetching fails.

    """

    def __init__(self, hass: HomeAssistant, api_client) -> None:
        """Initialize the ForecastUpdateCoordinator.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            api_client: The API client used to fetch forecast data.

        Initializes the coordinator with the given Home Assistant instance and API client. Sets
        the update interval to fetch forecasts every hour.

        """
        self.api_client = api_client
        super().__init__(
            hass,
            _LOGGER,
            name="ForecastUpdateCoordinator",
            update_interval=timedelta(minutes=60),  # Fetch forecasts every hour
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with asyncio.timeout(30):
                _LOGGER.debug("Fetching forecasts")
                await self.api_client.fetch_forecasts()
                # Assume fetch_forecasts updates self.api_client.locations
                locations = await self.api_client.locations
                self.async_set_updated_data(locations)
                return locations  # Return updated data if needed
        except TimeoutError as err:
            _LOGGER.error("Timeout error fetching forecasts: %s", str(err))
            return None
        except ServerDisconnectedError as err:
            _LOGGER.error("Server disconnected while fetching forecasts: %s", str(err))
            return None
        except ClientConnectorError as err:
            _LOGGER.error("Network error fetching forecasts: %s", str(err))
            return None
        except OSError as err:  # For other network-related errors
            _LOGGER.error("OSError while fetching forecasts: %s", str(err))
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error fetching forecasts: %s", str(err))
            return None


class MeasurementUpdateCoordinator(DataUpdateCoordinator):
    """Handle periodic fetching and updating of measurement data from the API client for Home Assistant.

    Methods:
    __init__: Initialize the coordinator with the given Home Assistant instance and API client.
    Sets the update interval to fetch measurements every 15 minutes.
    _async_update_data: Fetch new measurement data from the API client.
    Updates listeners with the fetched data. Logs and raises an UpdateFailed exception if fetching fails.

    """

    def __init__(self, hass: HomeAssistant, api_client) -> None:
        """Initialize the MeasurementUpdateCoordinator.

        Args:
            hass (HomeAssistant): The Home Assistant instance.
            api_client: The API client used to fetch measurement data.

        Sets the update interval to fetch measurements every 15 minutes.

        """
        self.api_client = api_client
        super().__init__(
            hass,
            _LOGGER,
            name="MeasurementUpdateCoordinator",
            update_interval=timedelta(
                minutes=15
            ),  # Fetch measurements every 15 minutes
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with asyncio.timeout(30):
                _LOGGER.debug("Fetching measurements")
                await self.api_client.fetch_measurements(
                    1
                )  # Fetch measurements for the last 1 hour
                # Assume fetch_measurements updates self.api_client.locations
                locations = await self.api_client.locations
                self.async_set_updated_data(locations)
                return locations  # Return updated data if needed
        except TimeoutError as err:
            _LOGGER.error("Timeout error fetching measurements: %s", str(err))
            return None
        except ServerDisconnectedError as err:
            _LOGGER.error(
                "Server disconnected while fetching measurements: %s", str(err)
            )
            return None
        except ClientConnectorError as err:
            _LOGGER.error("Network error fetching measurements: %s", str(err))
            return None
        except OSError as err:  # For other network-related errors
            _LOGGER.error("OSError while fetching measurements: %s", str(err))
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error fetching measurements: %s", str(err))
            return None


class LocationDataUpdateCoordinator(DataUpdateCoordinator):
    """Handle fetching and updating of location-specific data from forecast and measurement coordinators.

    This coordinator combines data from both forecast and measurement sources, ensuring
    up-to-date information for a specific location within Home Assistant.

    Args:
        hass (HomeAssistant): The Home Assistant instance.
        forecast_coordinator: Coordinator for fetching forecast data.
        measurement_coordinator: Coordinator for fetching measurement data.
        name (str): The name of the location to manage data for.

    Attributes:
        hass (HomeAssistant): The Home Assistant instance.
        forecast_coordinator: Coordinator for fetching forecast data.
        measurement_coordinator: Coordinator for fetching measurement data.
        name (str): The name of the location to manage data for.
        _location_data: Cached location data combining forecasts and measurements.

    """

    def __init__(
        self, hass: HomeAssistant, forecast_coordinator, measurement_coordinator, name
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"LocationDataUpdateCoordinator-{name}",
            update_interval=timedelta(minutes=15),
        )
        self.hass = hass
        self.forecast_coordinator = forecast_coordinator
        self.measurement_coordinator = measurement_coordinator
        self.name = name
        self._location_data = None

        # Listen for updates from child coordinators
        self.forecast_coordinator.async_add_listener(self._create_handle_update_task)
        self.measurement_coordinator.async_add_listener(self._create_handle_update_task)

    async def get_location_data(self):
        """Fetch data for this specific location."""
        # Retrieve latitude and longitude from hass.data
        try:
            entry = self._get_entry_by_name(self.name)
            if entry is None:
                raise ValueError(f"No config entry found for location {self.name}")

            latitude = entry.data.get("latitude")
            longitude = entry.data.get("longitude")

            measurement_data = (
                await self.measurement_coordinator.api_client.get_location_by_name(
                    self.name
                )
            )
            forecast_data = (
                await self.forecast_coordinator.api_client.get_location_by_name(
                    self.name
                )
            )

            # Ensure that data is available
            if not measurement_data or not forecast_data:
                _LOGGER.debug(
                    "Measurement or forecast data not yet available for %s", self.name
                )
                if measurement_data is None:
                    await self.measurement_coordinator.api_client.add_location(
                        name=self.name, latitude=latitude, longitude=longitude
                    )
                    await self.measurement_coordinator.async_request_refresh()
                    measurement_data = await self.measurement_coordinator.api_client.get_location_by_name(
                        self.name
                    )

                if forecast_data is None:
                    await self.forecast_coordinator.api_client.add_location(
                        name=self.name, latitude=latitude, longitude=longitude
                    )
                    await self.forecast_coordinator.async_request_refresh()
                    forecast_data = (
                        await self.forecast_coordinator.api_client.get_location_by_name(
                            self.name
                        )
                    )

                if not measurement_data or not forecast_data:
                    return None

            # Check if measurements and forecasts exist and are not empty
            if (
                "measurements" not in measurement_data
                or not measurement_data["measurements"]
            ):
                _LOGGER.debug("Measurement data list is empty for %s", self.name)
                return None
            _LOGGER.debug("Measurement data list is populated for %s", self.name)

            if "forecasts" not in forecast_data or not forecast_data["forecasts"]:
                _LOGGER.debug("Forecast data list is empty for %s", self.name)
                return None
            _LOGGER.debug("Forecast data list is populated for %s", self.name)

            self._location_data = {
                "measurements": measurement_data["measurements"][0],
                "forecasts": forecast_data["forecasts"][0],
            }
            return self._location_data

        except Exception as err:
            _LOGGER.error(f"Error fetching location data for {self.name}: {err!s}")
            return None

    async def _async_update_data(self):
        """Fetch data for this specific location."""
        return await self.get_location_data()

    async def _handle_update(self):
        """Handle updates from child coordinators."""
        if not self.measurement_coordinator.last_update_success:
            _LOGGER.debug(
                "Measurement data unavailable, marking location data as unavailable for %s",
                self.name,
            )
            self._location_data = None
            self.async_set_updated_data(None)
            return

        location_data = await self.get_location_data()
        if location_data:
            self.async_set_updated_data(location_data)
        else:
            _LOGGER.debug("Location data not yet available for %s", self.name)
            self._location_data = None
            self.async_set_updated_data(None)

    def _create_handle_update_task(self):
        """Create a task to handle updates from child coordinators."""
        self.hass.async_create_task(self._handle_update())

    def _get_entry_by_name(self, name):
        """Helper function to get config entry by name."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("name") == name:
                return entry
        return None
