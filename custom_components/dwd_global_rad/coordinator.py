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

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
            _LOGGER.error("Timeout error fetching forecasts: %s", err)
            raise UpdateFailed(f"Timeout error fetching forecasts: {err}") from err
        except OSError as err:  # For network-related errors
            _LOGGER.error("Network error fetching forecasts: %s", err)
            raise UpdateFailed(f"Network error fetching forecasts: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching forecasts: %s", err)
            raise UpdateFailed(f"Unexpected error fetching forecasts: {err}") from err


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
            _LOGGER.error("Timeout error fetching measurements: %s", err)
            raise UpdateFailed(f"Timeout error fetching measurements: {err}") from err
        except OSError as err:  # For network-related errors
            _LOGGER.error("Network error fetching measurements: %s", err)
            raise UpdateFailed(f"Network error fetching measurements: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching measurements: %s", err)
            raise UpdateFailed(
                f"Unexpected error fetching measurements: {err}"
            ) from err


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
        measurement_data = (
            await self.measurement_coordinator.api_client.get_location_by_name(
                self.name
            )
        )
        forecast_data = await self.forecast_coordinator.api_client.get_location_by_name(
            self.name
        )

        # Ensure that data is available
        if not measurement_data or not forecast_data:
            _LOGGER.debug(
                "Measurement or forecast data not yet available for %s", self.name
            )
            return None

        if "measurements" not in measurement_data or "forecasts" not in forecast_data:
            _LOGGER.debug(
                "Measurement or forecast data lists are empty for %s", self.name
            )
            return None

        self._location_data = {
            "measurements": measurement_data["measurements"][0],
            "forecasts": forecast_data["forecasts"][0],
        }
        return self._location_data

    async def _async_update_data(self):
        """Fetch data for this specific location."""
        return await self.get_location_data()

    async def _handle_update(self):
        """Handle updates from child coordinators."""
        location_data = await self.get_location_data()
        if location_data:
            self.async_set_updated_data(location_data)
        else:
            _LOGGER.debug("Location data not yet available for %s", self.name)

    def _create_handle_update_task(self):
        """Create a task to handle updates from child coordinators."""
        self.hass.async_create_task(self._handle_update())
